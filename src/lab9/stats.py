"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb, isfinite

import numpy as np
from scipy import stats as scipy_stats

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge labels must have equal lengths")
    if any(label not in ("PASS", POS) for label in (*human, *judge)):
        raise ValueError("labels must be PASS or FAIL")
    return {
        "tp": sum(h == POS and j == POS for h, j in zip(human, judge)),
        "fp": sum(h != POS and j == POS for h, j in zip(human, judge)),
        "fn": sum(h == POS and j != POS for h, j in zip(human, judge)),
        "tn": sum(h != POS and j != POS for h, j in zip(human, judge)),
    }


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    precision_denominator = cm["tp"] + cm["fp"]
    recall_denominator = cm["tp"] + cm["fn"]
    precision = cm["tp"] / precision_denominator if precision_denominator else 0.0
    recall = cm["tp"] / recall_denominator if recall_denominator else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = len(human)
    if not n:
        raise ValueError("kappa is undefined for an empty sample")
    observed = (cm["tp"] + cm["tn"]) / n
    human_fail = cm["tp"] + cm["fn"]
    human_pass = cm["fp"] + cm["tn"]
    judge_fail = cm["tp"] + cm["fp"]
    judge_pass = cm["fn"] + cm["tn"]
    expected = (human_fail * judge_fail + human_pass * judge_pass) / (n * n)
    if expected == 1:
        raise ValueError("kappa is undefined when expected agreement is 1")
    return (observed - expected) / (1 - expected)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    values = (observed_rate, sensitivity, specificity)
    if any(not isfinite(value) or not 0 <= value <= 1 for value in values):
        raise ValueError("observed rate, sensitivity, and specificity must be finite probabilities")
    denominator = sensitivity + specificity - 1
    if denominator == 0:
        raise ValueError("Rogan-Gladen estimate is undefined when sensitivity + specificity = 1")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / denominator))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    a_values, b_values = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a_values.ndim != 1 or b_values.ndim != 1 or a_values.size != b_values.size or not a_values.size:
        raise ValueError("paired samples must have the same non-zero length")
    if isinstance(n_resamples, bool) or not isinstance(n_resamples, int) or n_resamples < 1:
        raise ValueError("n_resamples must be positive")
    if not isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    if not np.isfinite(a_values).all() or not np.isfinite(b_values).all():
        raise ValueError("paired samples must contain only finite values")
    difference = a_values - b_values
    mean_difference = float(np.mean(difference))
    if np.all(difference == 0):
        return 0.0, 0.0, 0.0

    result = scipy_stats.bootstrap(
        (a_values, b_values),
        lambda left, right, axis: np.mean(left - right, axis=axis),
        paired=True,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="percentile",
        rng=np.random.default_rng(rng),
    )
    return mean_difference, float(result.confidence_interval.low), float(result.confidence_interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_pass_k_args(n, c, k)
    return 1.0 - comb(n - c, k) / comb(n, k) if k <= n - c else 1.0


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_pass_k_args(n, c, k)
    return comb(c, k) / comb(n, k) if k <= c else 0.0


def _validate_pass_k_args(n: int, c: int, k: int) -> None:
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (n, c, k)):
        raise ValueError("n, c, and k must be integers")
    if n <= 0 or not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("require n > 0, 0 <= c <= n, and 1 <= k <= n")
