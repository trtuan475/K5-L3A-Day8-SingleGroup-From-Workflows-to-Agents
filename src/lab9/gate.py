"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems: list[str] = []
    pr_rows, base_rows = pr.get("rows", []), base.get("rows", [])
    manifest = pr.get("manifest", {})
    seeds = manifest.get("seeds", [])
    item_count = manifest.get("items")
    if not isinstance(item_count, int) or item_count < 0 or len(pr_rows) != item_count * len(seeds):
        problems.append("row_count does not match manifest items × seeds")
    if len(set(seeds)) != len(seeds):
        problems.append("manifest contains duplicate seeds")

    def row_keys(rows: list[dict]) -> list[tuple[str, int]]:
        return [(str(row.get("item_id")), row.get("seed")) for row in rows]

    pr_keys, base_keys = row_keys(pr_rows), row_keys(base_rows)
    if len(pr_keys) != len(set(pr_keys)):
        problems.append("duplicate (item_id, seed) rows")
    if set(pr_keys) != set(base_keys):
        problems.append("(item_id, seed) set differs from baseline")

    metrics = pr.get("metrics", {})
    for metric_id, value in metrics.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
            problems.append(f"metric {metric_id} is not finite")
    if pr.get("evaluator_failures"):
        problems.append("evaluator_failures is non-empty")

    for metric in spec.get("metrics", []):
        metric_id = metric["id"]
        row_metric_present = any(metric_id in row for row in pr_rows)
        row_level_grader = metric.get("grader") and metric.get("grader") != "lab8.metrics.summarize"
        if row_metric_present or row_level_grader:
            for row in pr_rows:
                is_not_applicable = metric_id in (row.get("not_applicable") or [])
                if is_not_applicable:
                    if pr.get("shape") not in metric.get("not_applicable_shapes", []) or row.get(metric_id) is not None:
                        problems.append(f"row {row.get('item_id')}@{row.get('seed')} has invalid N/A for {metric_id}")
                        break
                    continue
                if metric_id not in row or row[metric_id] is None:
                    problems.append(f"row {row.get('item_id')}@{row.get('seed')} has missing {metric_id}")
                    break
                value = row[metric_id]
                if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
                    problems.append(f"row {row.get('item_id')}@{row.get('seed')} has non-finite {metric_id}")
                    break

    pr_slices = {key: tuple(sorted(set(row.get("slices") or [])))
                 for key, row in zip(pr_keys, pr_rows)}
    base_slices = {key: tuple(sorted(set(row.get("slices") or [])))
                   for key, row in zip(base_keys, base_rows)}
    if pr_slices != base_slices:
        problems.append("slice tags differ from baseline")
    if pr.get("shape") == base.get("shape"):
        pr_na = {key: tuple(sorted(row.get("not_applicable") or []))
                 for key, row in zip(pr_keys, pr_rows)}
        base_na = {key: tuple(sorted(row.get("not_applicable") or []))
                   for key, row in zip(base_keys, base_rows)}
        if pr_na != base_na:
            problems.append("not-applicable metric tags differ from baseline")

    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        current_metrics = {metric["id"]: metric for metric in spec.get("metrics", [])}
        for old in base_spec.get("metrics", []):
            metric_id = old["id"]
            current = current_metrics.get(metric_id)
            if current is None:
                problems.append(f"ratchet removed metric {metric_id}")
                continue
            old_threshold = old.get("threshold", {})
            new_threshold = current.get("threshold", {})
            if "min" in old_threshold and new_threshold.get("min", -math.inf) < old_threshold["min"]:
                problems.append(f"ratchet loosened {metric_id}.threshold.min")
            if "max" in old_threshold and new_threshold.get("max", math.inf) > old_threshold["max"]:
                problems.append(f"ratchet loosened {metric_id}.threshold.max")
            if old_threshold.get("no_significant_drop") and not new_threshold.get("no_significant_drop"):
                problems.append(f"ratchet removed {metric_id}.threshold.no_significant_drop")
            if old.get("blocking") and not current.get("blocking"):
                problems.append(f"ratchet made {metric_id} non-blocking")

        current_slices = {(entry.get("name"), entry.get("metric")): entry
                          for entry in spec.get("slices", [])}
        for old in base_spec.get("slices", []):
            key = old.get("name"), old.get("metric")
            current = current_slices.get(key)
            if current is None:
                problems.append(f"ratchet removed slice {key[0]}/{key[1]}")
                continue
            if "min" in old and current.get("min", -math.inf) < old["min"]:
                problems.append(f"ratchet loosened slice {key[0]}/{key[1]} min")
            if "max" in old and current.get("max", math.inf) > old["max"]:
                problems.append(f"ratchet loosened slice {key[0]}/{key[1]} max")
            if old.get("no_significant_drop") and not current.get("no_significant_drop"):
                problems.append(f"ratchet removed slice {key[0]}/{key[1]} no_significant_drop")
            if old.get("blocking") and not current.get("blocking"):
                problems.append(f"ratchet made slice {key[0]}/{key[1]} non-blocking")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked: list[str] = []
    lines: list[str] = []
    bootstrap = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric_id = entry["name"], entry["metric"]
        current = per_item(pr, metric_id, slice_name=name)
        baseline = per_item(base, metric_id, slice_name=name)
        metric = entry.get("metric", "")
        verdict = "ok"
        notes: list[str] = []
        if not current:
            verdict = "missing"
            notes.append("no PR rows")
        else:
            value = sum(current.values()) / len(current)
            if "min" in entry:
                notes.append(f"mean {value:.3f} min {entry['min']:.3f}")
                if value < entry["min"]:
                    verdict = "fail"
            if entry.get("no_significant_drop"):
                keys = sorted(set(current) & set(baseline))
                if not keys:
                    verdict = "missing"
                    notes.append("no paired baseline items")
                else:
                    delta, lo, hi = stats.paired_bootstrap(
                        [current[key] for key in keys],
                        [baseline[key] for key in keys],
                        n_resamples=bootstrap.get("n_resamples", 1000),
                        rng=bootstrap.get("rng", 2027),
                        confidence=bootstrap.get("confidence", 0.95),
                    )
                    notes.append(f"Δ {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]")
                    if hi < 0:
                        verdict = "fail"
        is_blocking = entry.get("blocking", False)
        if verdict != "ok" and is_blocking:
            blocked.append(f"slice:{name}/{metric}")
        label = "ok" if verdict == "ok" else ("BLOCK" if is_blocking else "warn")
        lines.append(f"  slice:{name}/{metric:<18} {'; '.join(notes):<46} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            is_not_applicable = (
                pr.get("shape") in m.get("not_applicable_shapes", [])
                and bool(pr.get("rows"))
                and all(mid in (row.get("not_applicable") or []) and row.get(mid) is None
                        for row in pr["rows"])
            )
            verdict = "n/a" if is_not_applicable else "missing"
            if is_not_applicable:
                note = f"not applicable to shape {pr.get('shape')}"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict not in ("ok", "n/a") and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING", "n/a": "N/A"}.get(
            verdict, "BLOCK" if m.get("blocking") else "warn"
        )
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
