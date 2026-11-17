# Báo cáo cá nhân — Trần Quốc Tuấn

## 1. Thông tin thành viên

- Họ tên: Trần Quốc Tuấn
- MSSV: 2A202603561
- Email: trtuan.475@gmail.com
- GitHub: trtuan475

## 2. Phần việc phụ trách

Làm cá nhân: triển khai workflow, single-agent và orchestrator; tích hợp handoff/trace; viết kiểm thử, chạy benchmark và crash suite; hoàn thiện báo cáo kỹ thuật.

## 3. Đóng góp cụ thể

- Hoàn thiện ba shape theo `RunResult` và trace contract.
- Giữ việc tính quote trong code, chuyển quote đầy đủ cho `durability.issue_refund`; không để shape tự ghi ledger.
- Giới hạn ReAct ở 8 bước và tool đọc; orchestrator dùng handoff allowlist, investigator chỉ đọc.
- Thêm kiểm thử trace không lộ canary/PII và ablation tắt ticket-delay override.
- Commit kỹ thuật: sẽ cập nhật sau khi commit.

## 4. Bằng chứng

- `tests/test_student_shape_trace_privacy.py::test_student_shape_trace_omits_claim_secrets`
- `tests/test_swarm_verification_ablation.py::test_disabling_ticket_delay_override_fixes_seed_55_claim`
- `src/reports/benchmark.json`; ví dụ run id: `R-workflow-C-001-s11`
- `src/reports/crash.json`: crash safety `20/20`
- Kiểm chứng cuối: `python -m pytest -q -o addopts=` cho 306 passed; `python -m lab8.check_submission` cho 0 FAIL, 1 WARN (chờ commit/hash).

## 5. Công cụ AI đã dùng

Đã dùng Copilot SDK trong VS Code để hỗ trợ triển khai shape, viết test và rà contract/báo cáo. Kết quả được kiểm tra bằng pytest, benchmark public, crash suite, smoke test và `lab8.check_submission`; cần tự đọc hiểu code và có thể giải thích các quyết định trong ADR khi được hỏi.

## 6. Tự đánh giá

Giải pháp chọn workflow vì đạt kết quả public tương đương single và orchestrator với chi phí mô phỏng thấp nhất. Giới hạn hiện tại là chỉ có corpus public 14 claim; chưa có `student_drop` để tự kiểm hidden. MockLLM và cost mô phỏng không đại diện cho model hay chi phí sản xuất.
