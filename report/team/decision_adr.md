# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: chờ commit cá nhân; cập nhật bằng `git rev-parse --short HEAD`
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (`src/reports/crash.json`)
- Secret leak / approval bypass: 0 / 0 trên bộ public; chưa chạy bộ hidden

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng 14 claim và 5 seed (70 trial/shape), workflow đạt pass rate 1.000, pass^5 1.000, variance 0 và cost/success mô phỏng 27.86 VND. Single và orchestrator cũng đạt pass rate 1.000 nhưng cost/success lần lượt là 30.20 và 55.71 VND; swarm đạt 0.986 với variance 0.000816 và cost 49.57 VND. Vì workflow là mức tự chủ thấp nhất và đáp ứng đầy đủ các ca public, đây là lựa chọn phù hợp nhất với nguyên tắc least autonomy.

## Có đáng đổi lấy multi-agent không

Với kết quả public hiện tại, không đổi sang multi-agent: không có cải thiện pass rate để bù chi phí cao hơn. Quyết định sẽ được xem xét lại nếu kiểm định hidden cho thấy workflow không đạt ngưỡng pass rate 0.75 nhưng một shape nhiều agent đạt ngưỡng, đồng thời vẫn qua các điều kiện must-pass và lợi ích ổn định đủ lớn so với chi phí.

## Trace và bằng chứng

Trace ghi run/claim id, trạng thái quan sát, tên tool được chọn, quote và thao tác gọi host; orchestrator ghi handoff đã sanitize cùng kết quả điều tra đã rút gọn. Không ghi ticket nguyên văn, claim/order row thô, parent secret, raw headers, SĐT, địa chỉ, ghi chú nội bộ hay tên hàng. Trace được ghi tại đường dẫn do `Trace` quản lý và được benchmark/grader quét cùng kết quả; kiểm thử regression C-010 kiểm tra các chuỗi cấm ở cả ba shape.

## Giới hạn

Benchmark chỉ dùng 14 claim public và MockLLM; chưa có `student_drop` nên chưa đo hidden pass rate. Giá là mô phỏng, không phải hóa đơn API; latency `unavailable`. Không ngoại suy kết quả public thành cam kết trên dữ liệu sản xuất.
