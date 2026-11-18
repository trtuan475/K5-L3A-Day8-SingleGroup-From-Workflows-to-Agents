# Judge audit

Replay command: `python -m lab9.judge --csv data/eval/<file>.csv --audit 5`.

| Criterion | n | κ | Precision | Recall | Floors (κ≥0.6, P≥0.8, R≥0.7) | Decision |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | pass | Use for tone only |
| helpful | 100 | 0.375 | 1.000 | 0.300 | fail | Do not use as a gate |

With `FAIL` as the positive class, `tone_ok` has TP=24, FP=4, FN=6, TN=66. Its observed failure rate is 0.28 and its Rogan–Gladen corrected estimate is 0.30. The helpful judge has TP=9, FP=0, FN=21, TN=70; observed 0.09 versus corrected 0.30. Its perfect precision is not sufficient: it misses 70% of human-labeled failures.

## Disagreement audit

| # | Case | Judge | Human | Who is right? | Rubric action |
|---|---|---|---|---|---|
| 1 | tone H-008: “Em đã hoàn tiền … nha, anh check giúp em.” | PASS | FAIL | Human | Treat informal `em`/`nha` with an unfamiliar customer as too familiar; don't equate friendliness with appropriate tone. |
| 2 | tone H-017: “Dạ, bạn ơi … rồi nha.” | PASS | FAIL | Human | Disallow `bạn ơi`/overfamiliar address in a support reply; judge must consider pronoun/register, not just polite particles. |
| 3 | tone H-029: “Vui lòng chờ … không cần nhắn thêm.” | PASS | FAIL | Human | Add a negative tone example for commands that discourage the customer from following up. |
| 4 | tone H-042: “Đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ.” | FAIL | PASS | Human | Do not require an apology when a concise reply is complete, respectful, and informative. |
| 5 | tone H-051: “LogiX đã refund 90.000đ … ạ.” | FAIL | PASS | Human | Accept the approved support vocabulary `refund`; English loanwords alone are not a tone failure. |
| 6 | helpful HL-015: says 55.000đ; ledger is 40.000đ | PASS | FAIL | Human | Amount correctness is a deterministic ledger assertion, never a helpfulness-judge decision. |
| 7 | helpful HL-016: long apology, says 55.000đ; ledger is 35.000đ | PASS | FAIL | Human | Length and apology cannot compensate for a wrong amount; separate helpfulness from factual/financial correctness. |
| 8 | helpful HL-020: says 90.000đ; ledger is 120.000đ | PASS | FAIL | Human | Add a hard rule that refund amounts must match the ledger. |
| 9 | helpful HL-028: says 50.000đ; ledger is 35.000đ | PASS | FAIL | Human | Repeated empathetic wording must not mask a wrong financial fact. |
| 10 | helpful HL-035: says 50.000đ; ledger is 35.000đ | PASS | FAIL | Human | Keep money correctness in code grading; helpfulness replay is not a release gate. |

## Conclusion

- Use the replayed tone judge only for tone after calibration; it clears all three floors, with residual false positives/negatives documented above.
- Reject the helpful judge as a gate. Its recall is 0.30, and it repeatedly accepts fluent replies with amounts that disagree with the ledger.
- Replay rows are public and are not held out. Recalibrate on fresh human-labeled examples before relying on a judge for release decisions.
