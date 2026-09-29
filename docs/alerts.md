# Alerts và Runbooks

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `fast_success_slo_breach`
- Severity: Critical
- Duration: 5 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: `fast_successful_requests`, mục tiêu 99.5% request hoàn tất trong 3000 ms trên cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: Tỷ lệ fast-success dưới 99.5% trong cửa sổ 5 phút liên tục, với ít nhất 20 request.
- Ảnh hưởng tới người dùng: Request chậm hoặc không hoàn tất đúng hạn; error budget có thể bị tiêu hao.
- Ba bước kiểm tra đầu tiên: 1) Kiểm tra latency P50/P95/P99 và TTFT trên dashboard. 2) Lọc `response_sent` và `request_failed` theo thời gian, đối chiếu `correlation_id`. 3) Mở trace tương ứng để xác định retrieval hay generation đang chậm.
- Mitigation tạm thời: Giảm concurrency hoặc lưu lượng đầu vào nếu quá tải; tạm chuyển về prompt production gần nhất đã biết ổn định nếu thay đổi prompt trùng thời điểm alert; tiếp tục theo dõi fast-success rate.
- Owner: `lab-operator`.

## Alert 2

- Tên: `elevated_request_error_rate`
- Severity: Critical
- Duration: 5 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: Error-rate guardrail tối đa 2%; lỗi request cũng không được tính là good event của SLO.
- Điều kiện và thời gian duy trì: Tỷ lệ `request_failed` trên `request_received` lớn hơn 2% trong cửa sổ 5 phút liên tục, với ít nhất 20 request.
- Ảnh hưởng tới người dùng: Người dùng có thể nhận lỗi thay vì câu trả lời.
- Ba bước kiểm tra đầu tiên: 1) Xem số request và error rate trong khoảng alert. 2) Phân nhóm `request_failed` theo `error_type`, rồi tìm log liên quan bằng `correlation_id`. 3) Mở trace tương ứng và kiểm tra span lỗi cùng các thay đổi gần đây.
- Mitigation tạm thời: Tắt scenario/feature gây lỗi nếu xác định được, giảm lưu lượng khi lỗi do quá tải, hoặc khôi phục cấu hình/prompt ổn định gần nhất; xác nhận error rate giảm sau xử lý.
- Owner: `lab-operator`.

## Alert 3

- Tên: `low_retrieval_success_rate`
- Severity: Warning
- Duration: 5 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: Retrieval success guardrail tối thiểu 90%.
- Điều kiện và thời gian duy trì: `tool_success_rate_pct` dưới 90% trong cửa sổ 5 phút liên tục, với ít nhất 10 retrieval attempts.
- Ảnh hưởng tới người dùng: Câu trả lời có thể thiếu tài liệu hỗ trợ hoặc request có thể thất bại.
- Ba bước kiểm tra đầu tiên: 1) Kiểm tra retrieval success rate và số attempts. 2) Lọc log theo `tool_name`/`tool_success` và nối request bằng `correlation_id`. 3) Kiểm tra trace retrieval span, latency và lỗi phụ thuộc tìm kiếm.
- Mitigation tạm thời: Khôi phục cấu hình/index retrieval gần nhất đã biết hoạt động; nếu phù hợp, tạm dùng fallback an toàn và thông báo rõ khi không có nguồn hỗ trợ.
- Owner: `lab-operator`.
