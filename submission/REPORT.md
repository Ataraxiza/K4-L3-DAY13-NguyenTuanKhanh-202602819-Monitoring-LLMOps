# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Tuấn Khanh
- **MSSV:** 2A202602819
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/Ataraxiza/K4-L3-DAY13-NguyenTuanKhanh-202602819-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**`day13-k4-l3a-monitoring-llmops-v1` (K4).
- **Tên project Langfuse cá nhân:** day13-k4-l3a-202602819

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log(latency, event, model).png`, `evidence/04-structured-log(timestamp).png`, `evidence/04-structured-log(env, feature, correlation_id).png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall(tree).png`, `evidence/07-trace-waterfall(timeline).png`, `evidence/07-trace-waterfall(graph).png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions(v1).png`, `evidence/09-prompt-versions(v2).png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-latency-traffic.png`, `evidence/11-dashboard-errors-cost.png`, `evidence/11-dashboard-tokens-quality.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log-ask.png`, `evidence/13-incident-log-retrieval.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | FAILED, Estimated Score 30/100 — 20/21 records thiếu required fields; 20/21 thiếu enrichment; 0 correlation ID | **PASSED — 100/100** trên file log mới; các request/response có required fields, enrichment và `correlation_id` | Log mới có structured fields đầy đủ và correlation ID cho request/response. |
| `validate_dashboard.py` | PASSED — 6/6 panel hợp lệ | **PASSED — 6/6 panel hợp lệ** | Dashboard contract vẫn hợp lệ với 6 panel: Latency, Traffic, Errors, Cost, Tokens và Quality. |
| `pytest` | PASSED — 22/22 tests | **PASSED — 22/22 tests** | Chạy bằng `python -m pytest -q`. |
| Số traces hợp lệ | 0 | **37 root traces** trong Langfuse hôm nay; 27 có `correlation_id`, 10 trace cũ thiếu metadata này | Số trace được đối chiếu trên Langfuse; trace challenge được liên kết với log thông qua `correlation_id`. |
| Số PII leak | 0 | **0 phát hiện** trong log mới | Email, số điện thoại và credit-card trong `message_preview` đã được redaction; `user_id` chỉ được ghi dưới dạng hash. |
| Latency P95 / TTFT P95 | Chưa đo | **2655 ms / 50 ms** trên 5 response của challenge `rag_slow` | Challenge tạo ra 5 response có latency 2652–2655 ms, vượt threshold 2000 ms. TTFT vẫn 50 ms, cho thấy độ trễ chính nằm ở retrieval/request processing. |
| Retrieval success rate | Chưa đo | **100% (5/5 attempts trong challenge)** | Cả 5 retrieval đều `tool_success=true`; `rag_slow` làm retrieval chậm nhưng không làm retrieval thất bại. |


## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `CorrelationIdMiddleware` nhận `x-request-id` nếu request đã gửi; nếu không, tạo `req-<8-hex>` từ UUID. Middleware bind ID vào structlog contextvars, gắn vào request và trả lại qua response header `x-request-id`; context được clear trước và sau request để tránh rò sang request khác.
- **Các metadata được ghi vào structured log:** Mỗi record có `ts`, `level`, `event`, `service`, `correlation_id`, `env`, `session_id`, `feature`, `model` và `user_id_hash`. `request_received` ghi `message_preview` đã scrub; `response_sent` ghi latency, TTFT, token, cost, quality và retrieval `tool_name`/`tool_success`; lỗi có `error_type` và thông tin payload đã xử lý.
- **Cách bảo đảm PII được scrub trước khi ghi:** `summarize_text()` scrub email, số điện thoại Việt Nam, CCCD và thẻ thanh toán trước khi tạo preview. `scrub_event` chạy trước file writer/JSON renderer để scrub chuỗi trong `payload` và `event`; user ID không ghi nguyên văn mà được SHA-256 hash rút gọn 12 ký tự.
- **Cách kiểm chứng kết quả:** `scripts/validate_logs.py` hiện PASSED 54/54 trên 54 records, không thiếu required fields/enrichment, có 28 unique correlation IDs và 0 potential PII leaks. Quét lại 54 records bằng `scrub_text()` của project cũng không phát hiện pattern PII; `python -m pytest -q` PASSED 22/22 tests.

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

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (K4).
- **Khoảng thời gian điều tra:** 2026-09-29 19:40:45.391–19:40:58.684 UTC, từ request đầu đến response cuối của incident. Cùng timeline có 10 response bình thường ngay trước đó (19:39:17.716–19:39:19.142 UTC) và 10 response bình thường ngay sau đó (19:42:03.934–19:42:05.357 UTC), nên trace incident được kẹp giữa hai nhóm trace bình thường trong một khoảng khoảng ba phút. Lưu ý: Log timestamp xài UTC, khác với giờ địa phương thực tế (Việt Nam).
- **Triệu chứng từ metrics:** 5 request; `latency_p50=2654 ms`, `latency_p95=2655 ms`, `latency_p99=2655 ms`, `ttft_p95=50 ms`; cả 5 request vượt challenge threshold 2000 ms, dù chưa vượt dashboard SLO line 3000 ms. Không có request error và retrieval success là 100%. Client quan sát khoảng 13.3 giây cho mỗi request do năm request đồng thời bị serialize.
- **Log line và correlation ID liên quan:** `response_sent` lúc `2026-09-29T19:40:48.047603Z`, `correlation_id=req-0ee9aeba`, `session_id=k4-l3a-challenge-s01`, `latency_ms=2655`, `ttft_ms=50`, `tool_success=true`; request tương ứng bắt đầu lúc `2026-09-29T19:40:45.390961Z` với cùng correlation ID.
- **Trace ID và span gây ảnh hưởng:** [Trace `262bd354c047d0798683d41ec9d446a3`](https://cloud.langfuse.com/project/cmumd5fsp14bhad0cggcr4izs/traces/262bd354c047d0798683d41ec9d446a3), cùng `correlation_id=req-0ee9aeba`. Root `lab-agent-run` kéo dài 2656 ms; span `retrieval` (`1aacc34d873bb113`) kéo dài 2500 ms, trong khi generation (`b90ab1ba4ff130e0`) kéo dài khoảng 153 ms.
- **Root cause:** Challenge bật `rag_slow`, khiến `retrieve()` ngủ 2.5 giây trong retrieval; riêng bước này đã vượt threshold 2 giây. Tác động client bị khuếch đại vì route `/chat` là async nhưng gọi `agent.run()` đồng bộ trên event loop, làm các request concurrency 5 chờ nối tiếp. Đây là nguyên nhân chậm có chủ đích của challenge, không phải lỗi retrieval (`tool_success=true`).
- **Fix action:** Đã tắt `rag_slow` sau workload và xác nhận mọi incident flag đều `false`. Với mã chạy thật, chuyển retrieval sang I/O async hoặc offload sang thread pool, đặt timeout và fallback để retrieval chậm không chặn event loop.
- **Preventive measure:** Theo dõi retrieval span latency và fast-success SLI theo ngưỡng; alert khi vượt latency budget; thêm load/regression test concurrency để phát hiện event-loop blocking và xác nhận timeout/fallback.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Chọn sử dụng structured logging kết hợp `correlation_id` và PII redaction ngay trước khi ghi log. Cách này giúp liên kết request/response với trace, đồng thời hạn chế việc dữ liệu nhạy cảm xuất hiện trong log. Đây cũng là cơ sở để validator có thể kiểm tra required fields, enrichment và PII.
- **Một lỗi/blocker đã gặp:** Challenge `rag_slow` làm latency tăng lên khoảng 2652–2655 ms. Ngoài độ trễ 2.5 giây của retrieval, việc route /chat gọi agent.run() đồng bộ trên async event loop khiến 5 request đồng thời bị serialize, làm thời gian client quan sát tăng đáng kể.
- **Cách tìm nguyên nhân và xử lý:** Tôi bắt đầu từ metrics để xác định latency tăng nhưng error rate và retrieval success vẫn bình thường. Sau đó dùng `correlation_id` để tìm request/response tương ứng trong structured log và mở trace trên Langfuse. Trace cho thấy span retrieval mất khoảng 2500 ms, trong khi generation chỉ khoảng 153 ms. Từ đó xác định `rag_slow` là nguyên nhân trực tiếp. Sau workload, tôi tắt incident flag và xác nhận `rag_slow` đã được disable.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cho biết có vấn đề gì và mức độ ảnh hưởng, ví dụ latency P95 tăng lên 2655 ms. Logs cho biết request nào và trong hoàn cảnh nào xảy ra vấn đề, thông qua `correlation_id`, session và các metadata liên quan. Traces cho biết thành phần/span nào gây ra độ trễ, từ đó có thể xác định retrieval chiếm phần lớn thời gian. Ba lớp này bổ trợ cho nhau thay vì hoạt động độc lập.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version giúp xác định chính xác prompt nào đã được sử dụng và cho phép promote/rollback giữa các version khi thay đổi prompt. Token và cost giúp theo dõi hiệu quả sử dụng model và chi phí request. SLO cung cấp ngưỡng vận hành để xác định khi nào hệ thống không đạt mục tiêu. Kết hợp các thông tin này giúp việc thay đổi prompt/model có thể được theo dõi, kiểm chứng và rollback có kiểm soát.
- **Điều quan trọng nhất đã học:** Tôi hiểu rõ hơn cách kết hợp Metrics, Logs và Traces để điều tra một vấn đề production-like thay vì chỉ nhìn vào một loại dữ liệu. Đặc biệt, latency cao không nhất thiết đồng nghĩa với request error: trong challenge này retrieval vẫn thành công 100%, nhưng span retrieval chậm đã làm toàn bộ request vượt threshold.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Kết quả latency và SLO trong bài lab được tính trên workload nhỏ nên chưa thể đại diện cho traffic production hoặc cửa sổ SLO 28 ngày. Phần xử lý retrieval trong mã hiện tại vẫn cần được cải thiện bằng async I/O hoặc thread pool, kết hợp timeout và fallback để tránh blocking event loop khi retrieval chậm.

## 9. Checklist trước khi nộp

- [X] Kết quả và evidence thuộc commit SHA cuối.
- [X] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [X] Incident evidence nối đúng metric → log → trace.
- [X] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [X] Repository chạy lại được theo README.
- [X] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [X] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
