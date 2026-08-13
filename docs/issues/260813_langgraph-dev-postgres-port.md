## 260813
* `langgraph dev`는 정상 실행된 것처럼 배너까지 찍히는데, LangSmith Studio에서 `Failed to initialize Studio` / `Error Failed to fetch`가 뜬다.
* claude 답변

Studio의 "Failed to fetch"는 CORS나 브라우저(mixed content) 문제가 아니라, **`langgraph dev` 서버가 이미 죽어 있어서** 생긴 증상입니다.

### 확인한 사실

#### 1. 포트 2024에 리스너가 없음
```
Get-NetTCPConnection -LocalPort 2024 -State Listen   # 결과 없음
Invoke-WebRequest http://127.0.0.1:2024/ok           # 원격 서버에 연결할 수 없습니다
```
배너는 찍혔지만 그 뒤 그래프 임포트 단계에서 프로세스가 죽었음.

#### 2. Postgres가 5432가 아닌 랜덤 포트에 떠 있음
```
docker ps
bookchatbot-postgres | Up (healthy) | 0.0.0.0:51382->5432/tcp
```
`src/graph.py`는 `localhost:${POSTGRES_PORT:-5432}`로 접속함:
```python
_conn_string = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@localhost:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
)
_conn = psycopg.Connection.connect(_conn_string, autocommit=True)
```
→ 5432에 아무것도 없으니 `connection timeout expired` → 서버 종료.
`docs/langgraph-cli.md`에 적어둔 그 증상과 동일.

#### 3. 왜 포트가 어긋났나 — `.env` 위치 문제 (근본 원인)
`.env`는 `C:\Users\holla\workspaces\.env` (워크스페이스 루트)에 있음. 프로젝트 안에는 없음.

* `graph.py` → `load_dotenv(find_dotenv())`. `find_dotenv()`는 **상위 디렉터리를 거슬러 올라가며 찾으므로** 루트 `.env`를 읽음 (`POSTGRES_PORT=5432`).
* `docker compose` → **상위 디렉터리를 타고 올라가지 않음.** 프로젝트 디렉터리(`-f docker/docker-compose.yaml`이므로 `docker/`)에 `.env`가 없어서 `${POSTGRES_PORT}`가 빈 문자열이 됨.

결과적으로 compose가 이렇게 해석함:
```yaml
ports:
  - :5432      # 호스트 포트 미지정 → 랜덤 배정 (51382)
```
```
docker compose -f docker/docker-compose.yaml config
    ports:
      - mode: ingress
        target: 5432       # published 항목이 아예 없음
        protocol: tcp
```
컨테이너 안에도 환경변수가 안 들어가 있음:
```
docker exec bookchatbot-postgres printenv POSTGRES_DB POSTGRES_USER   # 빈 값
```

> 그런데도 컨테이너가 healthy인 이유: `docker/postgres/data`에 예전 정상 실행 때 만들어진 데이터 디렉터리가 남아 있어서 initdb를 건너뛰었기 때문. 즉 DB 내용물은 멀쩡하고 **포트 매핑만** 어긋난 상태.

### 해결

`projects/chatbot`에서:
```
docker compose --env-file ../../.env -f docker/docker-compose.yaml up -d
docker ps          # 0.0.0.0:5432->5432/tcp 인지 확인
langgraph dev
```
* `--env-file` 경로는 **cwd 기준 상대경로**라서 `projects/chatbot`에서 실행할 때 `../../.env`.
* 설정이 바뀌었으므로 `up -d`가 컨테이너를 재생성함. 데이터는 `./postgres/data` 바인드 마운트라 유지됨.

#### 대안
`--env-file`을 매번 붙이는 게 번거로우면 `POSTGRES_*` 네 줄만 `docker/.env`로 복사해두면 됨. 대신 비밀번호가 저장되는 곳이 한 군데 더 늘어남.

### 참고
`langgraph.json`에 `"env"` 키가 없지만, `graph.py`가 직접 `load_dotenv(find_dotenv())`를 호출하고 있어서 동작에는 문제 없음.

### 교훈
* Studio의 `Failed to fetch`는 대부분 **서버가 안 떠 있다는 뜻**. 브라우저/CORS부터 의심하지 말고 `http://127.0.0.1:2024/ok`부터 찍어볼 것.
* `langgraph dev`는 배너를 먼저 출력하고 나서 그래프를 임포트하므로, **배너가 떴다고 정상 기동이 아님.**
* `find_dotenv()`(상위 탐색함)와 `docker compose`(상위 탐색 안 함)의 `.env` 탐색 규칙이 다르다는 점이 이번 문제의 핵심.
