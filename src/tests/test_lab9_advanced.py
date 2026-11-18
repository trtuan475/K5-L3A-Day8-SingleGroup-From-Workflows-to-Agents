"""M5-M7 self-check (Advanced/Expert). Run: python -m pytest -q -m student -o addopts= -k advanced
Public vectors only; the instructor grades with hidden ones."""
import copy
import math

import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def stats():
    from lab9 import stats

    return stats


@pytest.mark.parametrize("n,c,k,want", [(5, 5, 5, 1.0), (5, 0, 1, 0.0), (5, 2, 1, 0.4), (10, 3, 3, 1 - 35 / 120)])
def test_pass_at_k(stats, n, c, k, want):
    assert math.isclose(stats.pass_at_k(n, c, k), want, abs_tol=1e-9)


@pytest.mark.parametrize("n,c,k,want", [(5, 5, 5, 1.0), (5, 4, 5, 0.0), (5, 4, 3, 0.4), (10, 8, 2, 28 / 45)])
def test_pass_hat_k(stats, n, c, k, want):
    assert math.isclose(stats.pass_hat_k(n, c, k), want, abs_tol=1e-9)


def test_pass_k_rejects_bad_args(stats):
    for args in [(5, 6, 1), (5, 2, 0), (3, 1, 4)]:
        with pytest.raises(ValueError):
            stats.pass_at_k(*args)
        with pytest.raises(ValueError):
            stats.pass_hat_k(*args)


def _report(rows, metrics, items=4, seeds=(1, 2)):
    return {"manifest": {"eval_set_sha": "x", "items": items, "seeds": list(seeds)},
            "rows": rows, "metrics": metrics, "evaluator_failures": []}


ROWS = [{"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i < 2 else []}
        for i in range(4) for s in (1, 2)]
SPEC = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True,
                                               "threshold": {"min": 0.8}}]}


def test_integrity_flags_nan_and_dropped_rows():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    assert gate.integrity_check(base, base, SPEC) == []
    nan = _report(copy.deepcopy(ROWS), {"pass_rate": float("nan")})
    assert gate.integrity_check(nan, base, SPEC)
    dropped = _report(copy.deepcopy(ROWS[:-1]), {"pass_rate": 1.0})
    assert gate.integrity_check(dropped, base, SPEC)


def test_integrity_flags_loosened_spec():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    loose = copy.deepcopy(SPEC)
    loose["metrics"][0]["threshold"]["min"] = 0.5
    assert gate.integrity_check(base, base, loose, SPEC)
    assert gate.integrity_check(base, base, SPEC, SPEC) == []


def test_integrity_flags_missing_score_evaluator_failure_and_slice_relabel():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    changed = copy.deepcopy(base)
    changed["rows"][0]["pass_rate"] = None
    changed["rows"][0]["slices"] = ["money_movement"]
    changed["evaluator_failures"] = ["E-001@1:grader:crashed"]
    problems = gate.integrity_check(changed, base, SPEC)
    assert any("missing pass_rate" in problem for problem in problems)
    assert any("evaluator_failures" in problem for problem in problems)
    assert any("slice tags differ" in problem for problem in problems)


def test_integrity_flags_duplicate_pair():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    duplicate = copy.deepcopy(base)
    duplicate["rows"][-1] = copy.deepcopy(duplicate["rows"][-2])
    problems = gate.integrity_check(duplicate, base, SPEC)
    assert any("duplicate (item_id, seed)" in problem for problem in problems)
    assert any("set differs from baseline" in problem for problem in problems)


def test_swarm_reply_metric_is_explicitly_not_applicable():
    from lab9 import gate

    metric_id = "reply_amount_matches_ledger"
    rows = copy.deepcopy(ROWS)
    for row in rows:
        row[metric_id] = None
        row["not_applicable"] = [metric_id]
    report = _report(rows, {metric_id: None})
    report["shape"] = "swarm"
    spec = {"eval_set_version": "v1", "metrics": [{
        "id": metric_id, "kind": "capability", "grader": "code", "blocking": True,
        "threshold": {"min": 1.0}, "not_applicable_shapes": ["swarm"],
    }]}

    blocked, lines = gate.check(report, copy.deepcopy(report), spec)
    assert blocked == []
    assert "N/A" in lines[0]

    invalid = copy.deepcopy(report)
    invalid["rows"][0]["not_applicable"] = []
    blocked, lines = gate.check(invalid, report, spec)
    assert blocked == ["integrity"]
    assert any("missing reply_amount_matches_ledger" in line for line in lines)


def test_ci_check_treats_pass_hat_as_a_derived_metric():
    from lab9 import ci_check

    report = _report(copy.deepcopy(ROWS), {"reply_amount_matches_ledger": None, "pass_hat_5": 0.9})
    report["shape"] = "swarm"
    spec = {"metrics": [
        {"id": "reply_amount_matches_ledger", "kind": "capability", "blocking": True},
        {"id": "pass_hat_5", "kind": "capability", "blocking": True},
    ]}
    assert ci_check.check(report, report, spec) == []


def test_ratchet_rejects_removed_metrics_and_slices():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    previous = copy.deepcopy(SPEC)
    previous["slices"] = [{"name": "denial", "metric": "pass_rate", "min": 0.9,
                           "no_significant_drop": True, "blocking": True}]
    current = copy.deepcopy(SPEC)
    current["metrics"] = []
    current["slices"] = []
    problems = gate.integrity_check(base, base, current, previous)
    assert any("removed metric pass_rate" in problem for problem in problems)
    assert any("removed slice denial/pass_rate" in problem for problem in problems)


def test_slice_check_blocks_a_slice_below_floor():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    rows = copy.deepcopy(ROWS)
    for r in rows:
        if "denial" in r["slices"] and r["seed"] == 1:
            r["pass_rate"] = False
    spec = dict(SPEC, slices=[{"name": "denial", "metric": "pass_rate", "min": 0.9, "blocking": True}])
    blocked, _ = gate.slice_check(_report(rows, {"pass_rate": 0.75}), base, spec)
    assert blocked == ["slice:denial/pass_rate"]
