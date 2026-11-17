# Trace case: ticket overrides the database

Reproduce the trial and its control:

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
```

| Field | Finding |
|---|---|
| Trial | `seeded_regression C-002@11`; report run `E-seeded_regression-20261117-dc30` |
| Symptom | Lab 8 grader fails with `status resolved != denied`; ledger has 20,000 VND although the label expects no refund. |
| First wrong step | Event 3: `model_override`, payload `{"delay_days": 5}`. The ticket's claim replaces the database delay value. |
| Why it is first | Events 1–2 establish the handoff and a visible order. Neither changes the DB facts. Event 3 is the first event that contradicts the DB order. The subsequent quote/refund follow that altered value. |
| Failure mode | FM-03 `ticket_trust` (and resulting FM-02 denial bypass). |
| Control | `fixed C-002@11` has no `model_override`; it quotes 0, leaves the ledger at 0, and the Lab 8 grader passes. |
| Regression test | `tests/test_lab9_graders.py::test_trace_case_first_wrong_step_and_fixed_control` asserts the failing event and passing control. |
| Uncertainty | This deterministic MockLLM trace proves the seeded case, not the frequency of this failure on a real model. |

The failing trace event sequence is: handoff → investigator (`O-202` is visible) → `model_override` → quote 20,000 → refund history → reply. The fixed control is: handoff → investigator → quote 0 → reply. Keep the event index and payload in future reports; “the agent was confused” is not a trace diagnosis.

When investigating a different case, read the ledger before the reply. A fluent response does not prove that the correct amount was committed.
