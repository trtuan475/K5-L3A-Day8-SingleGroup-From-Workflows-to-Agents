# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 · Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri et al., “Why Do Multi-Agent LLM Systems Fail?”, 2025, https://arxiv.org/abs/2503.13657. Nghiên cứu thực nghiệm/preprint: taxonomy MAST xây từ trace MAS được gán nhãn. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Nguồn xác định 14 failure mode, gom thành 3 nhóm: system design issues, inter-agent misalignment và task verification; phân tích hơn 1,600 trace từ 7 framework. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận gốc thuộc các hệ thống/model/task trong MAST-Data; không chứng minh trực tiếp nguyên nhân trên claim giả lập này. Bộ lab chỉ có 14 claim public và MockLLM. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Với C-002/s55 cố định, tắt bước lấy delay từ ticket sẽ đổi kết quả sai `resolved, 20000` thành đúng `denied, 0`; model calls giữ nguyên, tool calls giảm 1 và cost giảm một tool call (10 VND mô phỏng). |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ claim C-002, seed 55, shape swarm, MockLLM, bộ tool, world, giá và evaluator. Biến duy nhất: vô hiệu hóa `parse_delay_days` trong swarm để loại ticket override; số tool call và cost là metric đầu ra. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi task verification: ticket khai 5 ngày nhưng order là 2 ngày. Đo status, proposal/refund, model/tool calls và cost baseline so với treatment. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m pytest -q tests/test_swarm_verification_ablation.py`
- Run id / file report: Baseline benchmark `R-swarm-C-002-s55` trong `src/reports/benchmark.json`; treatment và đối chiếu trong `src/tests/test_swarm_verification_ablation.py`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Đúng. Baseline trả `resolved, 20000`; khi tắt duy nhất ticket override, treatment trả `denied, 0` và không ghi refund. Cả hai có 3 model calls; baseline có 6 tool calls và cost 62.22 VND, treatment 5 tool calls và 52.20 VND. Benchmark nền cũng cho thấy C-002/s55 là lỗi swarm duy nhất: pass rate 69/70 = 0.986, pass^5 = 13/14 = 0.929, variance theo seed = 0.000816. Phân loại task verification là nhận định của nhóm, không phải nhãn do paper gán.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
