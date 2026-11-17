# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ `src/reports/benchmark.json` và `src/reports/crash.json`.

## 1. Thông tin nhóm

- Tên nhóm: SingleGroup (làm cá nhân)
- Thành viên: Trần Quốc Tuấn (xem `TEAM.md`)
- Commit chốt: chờ commit cá nhân; cập nhật sau khi chốt

## 2. Mục tiêu và cách tiếp cận

Bài toán là xác định quyền lợi theo dữ liệu order/policy và để host kiểm approval, cap theo order, idempotency trước khi ghi ledger. Một thành viên phụ trách toàn bộ ba shape, integration, kiểm thử và báo cáo. Cả bốn shape được so sánh trên cùng 14 claim, seed 11/22/33/44/55, MockLLM và bảng giá.

Nguyên tắc thiết kế là dùng mức tự chủ thấp nhất đáp ứng được yêu cầu. Ticket được xem là input không tin cậy; order row và policy hiện hành là nguồn sự thật; model không quyết định số tiền hay ghi refund.

## 3. Giải pháp

`workflow` là luồng Python cố định đọc claim/order rồi gọi `compute_compensation`. `single` dùng vòng ReAct giới hạn 8 bước và chỉ cho phép tool đọc; sau khi có quote, shape gọi host. `orchestrator` tạo handoff bằng allowlist, investigator chỉ đọc dữ liệu đã scope, còn orchestrator truyền quote đầy đủ cho host. Ở cả ba shape, host chịu trách nhiệm authorization, approval, cap và idempotency.

Trace chỉ ghi run/claim id, trạng thái, thao tác/tool, quote và dữ liệu điều tra đã rút gọn; không ghi ticket nguyên văn, secret, header, PII hay row thô. Test regression C-010 quét chuỗi cấm trong trace của cả ba shape.

## 4. Kết quả

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean/p95 steps |
|---|---:|---:|---:|---:|---:|---:|
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 27.86 | 2.64 / 3 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 30.20 | 6.29 / 7 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 55.71 | 4.36 / 5 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Benchmark có 70 trial/shape. Crash suite đạt 20/20. Public suite không ghi nhận leak hoặc approval bypass; hidden self-check chưa chạy vì chưa có `student_drop/`.

Nhóm chọn workflow: giữ mức tự chủ thấp nhất nhưng đạt cùng pass rate/pass^5 như single và orchestrator trên corpus public, đồng thời có cost/success thấp nhất. Swarm có biến động theo seed và lỗi C-002/s55 do tin delay từ ticket hơn order. Chi tiết lý do và research ablation nằm trong ADR/research card.

## 5. Khó khăn và cách xử lý

Lệnh pytest phải chạy trong `src/` theo hướng dẫn; chạy từ repo root không tìm được package `lab8`. Chuyển vào `src/` thì host suite và student matrix chạy thành công. Benchmark và crash report được sinh bằng module của lab, không chỉnh tay.

## 6. Tổng hợp đóng góp

Thành viên duy nhất là Trần Quốc Tuấn; vai trò và test regression được ghi trong `TEAM.md`. Báo cáo cá nhân là `report/team/2A202603561_TranQuocTuan.md`. Hash commit sẽ được cập nhật sau khi commit.

## 7. Hạn chế và hướng cải thiện

MockLLM không đại diện cho model sản xuất; giá token/tool là mô phỏng và latency `unavailable`. Corpus public nhỏ nên chưa chứng minh pass rate hidden ≥ 0.75. Quyết định cần được xem lại nếu workflow không đạt ngưỡng hidden nhưng một shape khác đạt must-pass và cải thiện pass ổn định đủ bù chi phí.

## 8. Tài liệu tham khảo

1. Cemri et al. (2025), “Why Do Multi-Agent LLM Systems Fail?”, arXiv:2503.13657, https://arxiv.org/abs/2503.13657.
2. LogiX-VN Lab 8, `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`.
