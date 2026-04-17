# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded secret `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` trong code.
2. Hardcoded `DATABASE_URL` chứa cả username/password.
3. `DEBUG = True` bật cứng, không lấy từ environment.
4. Dùng `print()` thay vì structured logging.
5. Log lộ secret qua `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`.
6. Không có endpoint `/health`.
7. Bind `host="localhost"` nên không phù hợp khi chạy trong container/cloud.
8. Hardcode `port=8000`, không đọc từ biến môi trường `PORT`.
9. `reload=True` chỉ phù hợp môi trường dev.
10. Không có graceful shutdown hay xử lý readiness.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trực tiếp trong code | Đọc từ `config.py` và environment variables | Có thể đổi cấu hình theo môi trường mà không sửa code |
| Secrets | Key và DB URL hardcode | Lấy từ env vars | Tránh lộ bí mật khi push code hoặc deploy |
| Port binding | `localhost:8000` cố định | `host=settings.host`, `port=settings.port` | Cloud platform inject `PORT`, container cần `0.0.0.0` |
| Logging | `print()` và log lộ secret | Structured JSON logging | Dễ truy vết, parse log, không làm lộ thông tin nhạy cảm |
| Health check | Không có | `GET /health` | Nền tảng cloud cần để kiểm tra liveness |
| Readiness | Không có | `GET /ready` | Load balancer biết khi nào instance sẵn sàng nhận traffic |
| Shutdown | Tắt đột ngột | `lifespan` + `SIGTERM` handler | Giảm lỗi khi redeploy hoặc scale down |
| Validation | Không kiểm tra payload tốt | Trả `422` nếu thiếu `question` | Tránh request lỗi làm hỏng luồng xử lý |
| CORS | Không có | Có middleware CORS | Hỗ trợ frontend gọi API an toàn |

### Checkpoint 1
- Hardcode secrets nguy hiểm vì có thể bị lộ ngay khi commit hoặc log.
- Environment variables giúp cùng một codebase chạy trên local, Docker, Railway, Render.
- Health check dùng để platform restart container khi service chết.
- Graceful shutdown giúp hoàn thành request đang chạy trước khi process dừng.

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image của bản develop là `python:3.11`.
2. Working directory là `/app`.
3. `COPY requirements.txt` trước để tận dụng Docker layer cache. Khi code thay đổi mà dependencies không đổi thì Docker không phải cài lại toàn bộ packages.
4. `CMD` là lệnh mặc định có thể bị override khi chạy container; `ENTRYPOINT` biến container thành một executable cố định hơn.

### Exercise 2.3: Multi-stage build
- Stage 1 `builder`: cài build dependencies (`gcc`, `libpq-dev`) và Python packages.
- Stage 2 `runtime`: chỉ copy packages và source code cần để chạy app.
- Image nhỏ hơn vì không mang theo toàn bộ build tools và layer trung gian.

### Exercise 2.4: Docker Compose stack
- Services trong `02-docker/production/docker-compose.yml`:
  - `agent`: FastAPI agent
  - `redis`: cache/session store
  - `qdrant`: vector database
  - `nginx`: reverse proxy và load balancer
- Chúng giao tiếp qua network `internal`.
- `nginx` là cổng vào public, chuyển traffic tới `agent`.
- `agent` kết nối `redis` qua `redis://redis:6379/0` và `qdrant` qua `http://qdrant:6333`.

### Exercise 2.3: Image size comparison
- Develop: cần đo bằng `docker images agent-develop`
- Production: cần đo bằng `docker images agent-production`
- Nhận xét dự kiến: production nhỏ hơn đáng kể nhờ `python:3.11-slim` + multi-stage build.

### Checkpoint 2
- Dockerfile bản basic minh họa đủ quy trình build image.
- Multi-stage build giúp giảm kích thước và bề mặt tấn công.
- Docker Compose orchestration giúp chạy nhiều service bằng một lệnh.
- Debug container bằng `docker logs`, `docker exec`, `docker inspect`, `docker compose ps`.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Các bước đúng:
  1. `npm i -g @railway/cli`
  2. `railway login`
  3. `railway init`
  4. `railway variables set PORT=8000`
  5. `railway variables set AGENT_API_KEY=my-secret-key`
  6. `railway up`
  7. `railway domain`
- Sau khi có URL public, cần test:
  - `curl https://your-domain/health`
  - `curl https://your-domain/ask ...`

### Exercise 3.2: Compare `render.yaml` vs `railway.toml`
| Item | `railway.toml` | `render.yaml` |
|------|----------------|---------------|
| Format | TOML | YAML |
| Deployment style | Config cho một service Railway | Blueprint mô tả nhiều service |
| Build | `builder = "NIXPACKS"` hoặc Dockerfile auto-detect | `buildCommand` rõ ràng |
| Start command | `startCommand` | `startCommand` |
| Health check | `healthcheckPath` | `healthCheckPath` |
| Env vars | Set qua CLI/dashboard | Khai báo ngay trong `envVars`, có `generateValue`, `sync: false` |
| Infra as code | Gọn cho Railway | Mạnh hơn cho nhiều service như web + redis |

### Exercise 3.3: Cloud Run CI/CD understanding
- `cloudbuild.yaml` mô tả pipeline: test -> build Docker image -> push lên registry -> deploy Cloud Run.
- `service.yaml` mô tả hạ tầng chạy thật:
  - autoscaling min/max
  - resources CPU/RAM
  - env vars và secret bindings
  - liveness/startup probes

### Checkpoint 3
- Cần deploy thành công ít nhất 1 platform và lưu public URL thật.
- Cần biết set env vars qua dashboard hoặc CLI.
- Có thể xem logs bằng `railway logs` hoặc log viewer trên Render/Cloud Run.

## Part 4: API Security

### Exercise 4.1: API Key authentication
- API key được check trong `verify_api_key()` ở `04-api-gateway/develop/app.py`.
- Nếu thiếu key -> `401 Missing API key`.
- Nếu sai key -> `403 Invalid API key`.
- Rotate key bằng cách đổi giá trị `AGENT_API_KEY` trong environment/platform secret rồi restart/redeploy service.

### Exercise 4.2: JWT authentication
- Flow:
  1. Client gửi username/password tới `/auth/token`
  2. Server kiểm tra credentials bằng `authenticate_user()`
  3. Server tạo JWT bằng `create_token(username, role)`
  4. Client gọi `/ask` với header `Authorization: Bearer <token>`
  5. `verify_token()` decode token, kiểm tra signature và expiry
- Token chứa:
  - `sub`: username
  - `role`
  - `iat`
  - `exp`

### Exercise 4.3: Rate limiting
- Algorithm dùng: Sliding Window Counter với `deque` timestamps.
- User thường: `10 req/phút`.
- Admin: `100 req/phút`.
- Bypass limit cho admin bằng cách dùng `rate_limiter_admin` thay vì `rate_limiter_user`.

### Exercise 4.4: Cost guard implementation
- `cost_guard.py` hiện là in-memory demo:
  - user budget: `$1/day`
  - global budget: `$10/day`
  - check trước khi gọi LLM bằng `check_budget()`
  - ghi usage sau khi gọi LLM bằng `record_usage()`
- Với Redis production version, có thể dùng key theo tháng như pseudo-code trong lab:

```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False

    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)
    return True
```

### Checkpoint 4
- Đã hiểu API key auth, JWT flow, rate limiting, cost guard.
- Điểm cần nâng từ demo lên production: chuyển in-memory state sang Redis.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
- `GET /health`: kiểm tra liveness, trả JSON `status`, `uptime`, `checks`.
- `GET /ready`: kiểm tra readiness, trả `503` nếu app chưa ready hoặc dependency lỗi.

### Exercise 5.2: Graceful shutdown
- `lifespan` đặt `_is_ready = False` khi shutdown.
- Middleware đếm `_in_flight_requests`.
- App chờ tối đa 30 giây để request đang xử lý hoàn tất.
- `signal.signal(signal.SIGTERM, handle_sigterm)` để ghi log lúc orchestrator gửi SIGTERM.

### Exercise 5.3: Stateless design
- Anti-pattern: lưu `conversation_history = {}` trong memory process.
- Giải pháp đúng: lưu session/history trong Redis.
- Ở `05-scaling-reliability/production/app.py`, session được lưu bằng:
  - `save_session()`
  - `load_session()`
  - `append_to_history()`
- Lợi ích: request kế tiếp có thể đi tới instance khác mà vẫn đọc được cùng history.

### Exercise 5.4: Load balancing
- Stack gồm:
  - `agent`
  - `redis`
  - `nginx`
- Chạy:

```bash
docker compose up --scale agent=3
```

- Kỳ vọng:
  - nhiều instance agent cùng chạy
  - nginx phân tải request
  - response có trường `served_by` cho biết instance nào xử lý

### Exercise 5.5: Test stateless
- `test_stateless.py` gửi nhiều request tới `http://localhost:8080/chat`
- Script kiểm tra:
  - có nhiều `served_by` khác nhau
  - `session_id` giữ nguyên
  - history vẫn đầy đủ qua endpoint `/chat/{session_id}/history`

### Checkpoint 5
- Health/readiness giúp orchestrator quyết định restart hoặc route traffic.
- Graceful shutdown giảm lỗi khi rolling deploy.
- Stateless + Redis là điều kiện cần để scale ngang nhiều instances.

## Part 6: Final Project

### Current status of provided solution
- `06-lab-complete/check_production_ready.py` hiện pass `20/20`.
- `06-lab-complete/app/main.py` đã có:
  - config từ env
  - API key auth
  - in-memory rate limiting
  - cost guard
  - `/health`, `/ready`, `/metrics`
  - structured logging
  - graceful shutdown qua lifespan + SIGTERM hook
- Deliverable này phù hợp làm nền để tiếp tục deploy.

### Commands I should run to validate locally
```bash
cd /home/khvavuong/Documents/VinAction/Day12/day12_ha-tang-cloud_va_deployment

# Part 1
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py

# Part 2
cd /home/khvavuong/Documents/VinAction/Day12/day12_ha-tang-cloud_va_deployment
docker build -f 02-docker/develop/Dockerfile -t agent-develop .
docker run -p 8000:8000 agent-develop

# Part 4
cd 04-api-gateway/develop
AGENT_API_KEY=my-secret-key python app.py

# Part 6 readiness check
cd /home/khvavuong/Documents/VinAction/Day12/day12_ha-tang-cloud_va_deployment/06-lab-complete
python check_production_ready.py
```

## Remaining items I still need to fill manually
1. Kết quả thực tế của các lệnh `curl` nếu giảng viên yêu cầu paste output.
2. Kích thước image thật từ `docker images`.
3. Public URL Railway/Render sau khi deploy.
4. Screenshots deployment dashboard và service running.
