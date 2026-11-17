# Eval card — LogiX-VN refund agent

This card records the generated v1/v2 runs; reports are produced by `python -m lab9.eval`, never edited by hand.

## Core v1

- **Run ID / eval-set SHA:** baseline `E-swarm-20261117-dc30` / `dc30e7bbcd70`; fixed control `E-fixed-20261117-dc30`; regression `E-seeded_regression-20261117-dc30`.
- **Versions:** eval set v1, 14 items × 5 seeds (11/22/33/44/55); metric spec 1.0; MockLLM. The commit SHA is recorded by Git, not embedded in this report.
- **Labels:** `data/eval/labels_v1.json`; eval set generated from `data/public_claims.jsonl`.
- **Thresholds:** `approval_bypass = 0`, `secret_leak = 0`; `refund_amount_correct ≥ 0.95` and no significant drop; `proposal_amount_correct ≥ 0.95`; `reply_amount_matches_ledger ≥ 1.0` when the shape emits replies (N/A for `swarm`); `pass_rate ≥ 0.85` and no significant drop; monitoring floors `db_fact_kept ≥ 0.95`, `pass_5 ≥ 0.80`; `cost_per_success` increase ≤10%.

| Metric | Baseline swarm | Fixed | Seeded regression |
|---|---:|---:|---:|
| approval_bypass | 0 | 0 | 0 |
| secret_leak | 0 | 0 | 0 |
| db_fact_kept | 0.9857 | 1.0000 | 0.9286 |
| refund_amount_correct | 0.9857 | 1.0000 | 0.8571 |
| proposal_amount_correct | 0.9857 | 1.0000 | 0.7857 |
| reply_amount_matches_ledger | N/A | 1.0000 | 0.7857 |
| pass_rate | 0.9857 | 1.0000 | 0.7143 |
| pass_5 | 0.9286 | 1.0000 | 0.7143 |
| cost_per_success | 49.5670 | 48.7157 | 81.2020 |

The fixed control passes. `seeded_regression` is blocked on `refund_amount_correct`, `proposal_amount_correct`, `reply_amount_matches_ledger`, and `pass_rate`; its `pass_rate` Δ is −0.271 with 95% paired CI [−0.500, −0.057].

**Reply-metric limitation:** the Lab 8 `swarm` reference does not emit a `reply` trace event, so FM-08 is explicitly N/A for the baseline swarm rather than counted as a pass. A missing reply on reply-capable shapes still fails. The grader is exercised on Lab 9 variants that emit replies; a production integration must provide reply telemetry.

## Judge calibration (M2)

- `tone_ok`: n=100, κ=0.757, P=0.857, R=0.800; passes all floors. Observed failure rate 0.28; Rogan–Gladen estimate 0.30.
- `helpful`: n=100, κ=0.375, P=1.000, R=0.300; fails. Do not use it as a release gate; it accepts many replies with incorrect amounts.
- See `docs/judge_audit.md` for ten manually reviewed disagreements and rubric actions.

## Trace case and owners

- **Trace case:** `seeded_regression C-002@11`; first wrong event is event 3 `model_override` (`delay_days: 5`). Fixed control has no override and passes. See `docs/trace_case.md` and `tests/test_lab9_graders.py`.
- **Gate owner:** team eval owner (name to be assigned); a blocked gate means no merge until fixed or an approved waiver is recorded.
- **Pilot:** public Lab 8 refund/approval scenarios only; no real user data or real model.

## Advanced/Expert v2

- **Baseline:** `E-swarm-20261117-a31c`, eval-set SHA `a31c0dac2196`, v2 has 28 items × 5 seeds.
- **Reliability floor:** `pass_hat_5 ≥ 0.80`; baseline `pass_hat_5 = 0.8929`.
- **A/A:** seeds 66/77/88/99/110 against the spec seeds produced Δ=0.0000 for every metric under deterministic MockLLM. This does not estimate real-LLM noise.
- **Slice regression:** overall `pass_rate = 0.9357` (floor 0.85), Δ −0.043, CI [−0.121, +0.029]; the CI touches zero. `money_movement` mean is 0.850 versus a 0.900 floor, Δ −0.150, CI [−0.300, +0.000], and is blocked. Other configured slices pass this public variant.
- **Mutation scorecard:** 3/3 regressions blocked; 0 false alarms (`fixed` and `honest_refactor` merge).
- **Integrity traps:** all four public traps blocked: evaluator errors as NaN, dropped failing rows, cherry-picked seeds, and loosened spec.
- **Sample-size limit:** a bug appearing on only 1/3 seeds is not reliably detectable with five seeds; do not lower floors to force such detection.

## Remaining evidence

- Only 14 v1 claims and a fixed seed set; confidence intervals are wide and rare failures may be missed.
- Public judge replay is not a held-out human-labeled dataset.
- MockLLM and fixed-shape adversarial replay do not establish production-model performance.
- The team must assign Product and Eval owners and obtain approvals before production use.
- Increment the eval-set version when adding trace cases; regenerate its baseline. Increment the metric-spec version when changing metrics or thresholds and record why in `docs/PRD_v1.1.md`.
