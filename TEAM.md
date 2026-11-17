# Team

## Thông tin nhóm

- Tên nhóm: SingleGroup (làm cá nhân)
- Lớp: L3A
- Repo theo quy ước nộp: `K5-L3A-DAY08-SingleGroup-FromWorkflowsToAgents`
- URL repo hiện tại: https://github.com/trtuan475/K5-L3A-Day8-SingleGroup-From-Workflows-to-Agents
- Nhánh nộp, commit chốt: sẽ cập nhật sau khi commit và đổi tên repo theo [SUBMISSION.md](SUBMISSION.md)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Trần Quốc Tuấn | 2A202603561 | trtuan.475@gmail.com | trtuan475 | Phụ trách toàn bộ shape, tích hợp, kiểm thử và báo cáo |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Trần Quốc Tuấn | Toàn bộ bài lab (cá nhân) | Chờ commit cá nhân; cập nhật hash sau khi commit | `test_student_shape_trace_privacy.py::test_student_shape_trace_omits_claim_secrets`; `test_swarm_verification_ablation.py::test_disabling_ticket_delay_override_fixes_seed_55_claim` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603561_TranQuocTuan

### Phần việc phụ trách

- Cá nhân: triển khai workflow, single-agent và orchestrator; tích hợp trace/handoff; kiểm thử, benchmark và báo cáo.

### Đóng góp cụ thể

- Hoàn thiện ba shape theo contract chung, chuyển quote đầy đủ cho host, chuyển tiếp crash injection và giới hạn trace/handoff theo dữ liệu cần thiết.
- Thêm kiểm thử regression bảo đảm trace của ba shape không chứa canary secret hay các chuỗi PII của C-010.

### Bằng chứng

- `src/tests/test_student_shape_trace_privacy.py::test_student_shape_trace_omits_claim_secrets`
- `src/reports/benchmark.json`, `src/reports/crash.json`
- Commit: sẽ cập nhật sau khi commit.
