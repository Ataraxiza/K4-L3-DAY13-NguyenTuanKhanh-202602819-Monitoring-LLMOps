# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Tuấn Khanh
- **MSSV:** 2A202602819
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/Ataraxiza/K4-L3-DAY13-NguyenTuanKhanh-202602819-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** day13-k4-l3a-202602819

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | FAILED, Estimated Score 30/100 — 20/21 records thiếu required fields; 20/21 thiếu enrichment; 0 correlation ID |  | |
| `validate_dashboard.py` | PASSED — 6/6 panel hợp lệ | | |
| `pytest` | PASSED — 22/22 tests | | |
| Số traces hợp lệ | 0 | | |
| Số PII leak | 0 | | |
| Latency P95 / TTFT P95 | Chưa đo | | |
| Retrieval success rate | Chưa đo | | |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
- **Các metadata được ghi vào structured log:**
- **Cách bảo đảm PII được scrub trước khi ghi:**
- **Cách kiểm chứng kết quả:**

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Các trace được tạo bằng `LabAgent.run()` của project hiện tại, sử dụng Langfuse client từ `app.tracing.get_langfuse_client()`. Tôi chạy cùng một input với `LANGFUSE_PROMPT_LABEL=baseline` và `candidate`, sau đó dùng trace ID được trả về để mở trace trong Langfuse. Trace được kiểm tra trong đúng project Langfuse cá nhân `day13-k4-l3a-202602819`.
- **Cấu trúc root/retrieval/generation observations:** Mỗi request tạo một root trace/observation. Bên trong request có observation `retrieval` cho bước lấy tài liệu/context và observation `generation` cho bước gọi LLM. Prompt được resolve trước khi generation chạy; thông tin `prompt_name`, `prompt_label`, `prompt_version` và `prompt_source` được ghi vào metadata để truy xuất prompt đã sử dụng.
- **Cách nối trace với log:**Request sử dụng `correlation_id` để liên kết application log với request/trace tương ứng. Với evidence prompt versioning, tôi sử dụng `prompt-versioning-baseline` cho request baseline và `prompt-versioning-candidate` cho request candidate. Trace ID được lưu lại từ Langfuse và dùng để mở trực tiếp trace tương ứng.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** v1 / `baseline`
- **Version/label candidate:** v2 / `candidate`
- **Trace ID của mỗi version:** cùng input `How does prompt versioning support rollback?`; baseline: [2556d447800d3538767c868c857cb9d8](https://cloud.langfuse.com/project/cmumd5fsp14bhad0cggcr4izs/traces/2556d447800d3538767c868c857cb9d8), candidate: [36703e3a078a5d084b203137a9661ac8](https://cloud.langfuse.com/project/cmumd5fsp14bhad0cggcr4izs/traces/36703e3a078a5d084b203137a9661ac8)
- **Cách promote và rollback `production`:** Promote/rollback được thực hiện bằng Langfuse Python SDK thông qua `update_prompt(name, version, new_labels=...)`. Tôi chuyển label `production` sang v2, chạy request và kiểm tra trace có `prompt_version=2`; sau đó chuyển `production` về v1, chạy request lần nữa và kiểm tra trace có `prompt_version=1`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `config/dashboard.yaml` định nghĩa latency P50/P95/P99 và TTFT P95, request traffic, error rate và retrieval success, cost, input/output tokens, quality proxy. Nguồn là `data/logs.jsonl`, time range 60 phút, refresh 30 giây; `scripts/validate_dashboard.py` xác nhận 6/6 panel hợp lệ.
- **SLO và lý do chọn:** `fast_successful_requests` yêu cầu ít nhất 99.5% request hoàn tất trong 3000 ms trên cửa sổ 28 ngày. Mốc 3 giây là giới hạn latency hướng người dùng; log CP1 hiện có 10/10 response dưới mốc này nhưng mẫu nhỏ, không đại diện cho cửa sổ 28 ngày.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; với `N` request trong 28 ngày, budget là `0.005 × N` request chậm hoặc thất bại. Ví dụ 10,000 request cho phép tối đa 50 request không đạt. SLI là event-based nên không diễn giải budget này thành giờ downtime.
- **Ba alert và runbook tương ứng:** `fast_success_slo_breach` (fast-success <99.5%, tối thiểu 20 request/5 phút, Critical), `elevated_request_error_rate` (error rate >2%, tối thiểu 20 request/5 phút, Critical), `low_retrieval_success_rate` (`tool_success_rate_pct` <90%, tối thiểu 10 attempts/5 phút, Warning). Cả ba gửi Slack, owner `lab-operator`; quy trình kiểm tra và mitigation nằm tại [docs/alerts.md](../docs/alerts.md#alert-1), [Alert 2](../docs/alerts.md#alert-2), [Alert 3](../docs/alerts.md#alert-3).

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
