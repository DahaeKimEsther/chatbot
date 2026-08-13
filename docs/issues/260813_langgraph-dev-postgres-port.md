## 260813
* `langgraph dev`는 정상 실행된 것처럼 배너까지 찍히는데, LangSmith Studio에서 `Failed to initialize Studio` / `Error Failed to fetch`가 뜬다.
* claude 답변

---

## 요약

**Postgres는 51382 포트에 떠 있는데 `graph.py`는 5432로 접속하려다 타임아웃 → 그래프 로드 실패 → `langgraph dev` 서버 종료 → Studio가 붙을 서버가 없어서 `Failed to fetch`.**

포트가 어긋난 이유는 **같은 `.env` 파일을 한쪽은 읽고 한쪽은 못 읽어서**임.
`.env`는 `workspaces/.env` (프로젝트보다 두 단계 위)에 있음.

| | `.env` 탐색 방식 | 결과 |
|---|---|---|
| `docker compose` | 상위 디렉터리로 **안 올라감** → 못 읽음 | `${POSTGRES_PORT}`가 빈 문자열 → `ports: - :5432` → 호스트 포트 랜덤 배정 (51382) |
| `graph.py`의 `find_dotenv()` | 상위 디렉터리로 **올라감** → 읽음 | `POSTGRES_PORT=5432` → `localhost:5432`로 접속 시도 |

`docker-compose.yaml`에는 `${POSTGRES_PORT}:5432`로 제대로 적혀 있음. 랜덤 포트는 의도가 아니라 변수가 비어서 생긴 사고임.

**해결:** compose에게 `.env` 위치를 명시해준다.
```
docker compose --env-file ../../.env -f docker/docker-compose.yaml up -d
```

**부수적 원인:** 이 어긋남이 *서버 전체를 죽이는* 수준이 된 건 `graph.py`가 모듈 최상단(import 시점)에서 DB에 접속하기 때문. 포트를 맞추면 당장은 해결되지만, 구조상 DB가 흔들릴 때마다 같은 식으로 죽음. → 맨 아래 "추가로 볼 것" 참고

---

## 상세

요약의 인과 체인을 원인 → 결과 순서로 하나씩 근거와 함께.

> `.env` 탐색 차이 → 포트 불일치 → 접속 타임아웃 → 그래프 로드 실패 → 서버 종료 → Studio `Failed to fetch`

### 1. `.env` 탐색 차이 (근본 원인)

`.env`는 `C:\Users\holla\workspaces\.env` (워크스페이스 루트)에 있음. 프로젝트 안에는 없음.
```
POSTGRES_DB=bookchatbot
POSTGRES_USER=bookchatbot_user
POSTGRES_PASSWORD=***
POSTGRES_PORT=5432
```

* `graph.py` → `load_dotenv(find_dotenv())`. `find_dotenv()`는 **상위 디렉터리를 거슬러 올라가며 찾으므로** 루트 `.env`를 읽음.
* `docker compose` → **상위 디렉터리를 타고 올라가지 않음.** 프로젝트 디렉터리(`-f docker/docker-compose.yaml`이므로 `docker/`)에 `.env`가 없어서 변수가 전부 빈 문자열이 됨.

compose가 변수를 못 읽었다는 증거 — 컨테이너 안에 환경변수가 안 들어가 있음:
```
docker exec bookchatbot-postgres printenv POSTGRES_DB POSTGRES_USER   # 빈 값
```

### 2. → 포트 불일치

`docker-compose.yaml`은 `${POSTGRES_PORT}:5432`로 제대로 적혀 있지만, 변수가 비었으므로 compose는 이렇게 해석함:
```yaml
ports:
  - :5432      # 호스트 포트 미지정 → 랜덤 배정
```
```
docker compose -f docker/docker-compose.yaml config
    ports:
      - mode: ingress
        target: 5432       # published 항목이 아예 없음
        protocol: tcp
```
그래서 실제로 뜬 포트는 51382:
```
docker ps
bookchatbot-postgres | Up (healthy) | 0.0.0.0:51382->5432/tcp
```

반면 `graph.py`는 `.env`를 읽었으므로 5432로 감:
```python
_conn_string = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@localhost:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
)
```

> 변수가 다 비었는데도 컨테이너가 healthy인 이유: `docker/postgres/data`에 예전 정상 실행 때 만들어진 데이터 디렉터리가 남아 있어서 initdb를 건너뛰었기 때문. 즉 DB 내용물은 멀쩡하고 **포트 매핑만** 어긋난 상태.

### 3. → 접속 타임아웃 → 그래프 로드 실패 → 서버 종료

5432에는 아무것도 없으니 `graph.py:136`에서 타임아웃:
```
File "C:\Users\holla\workspaces\projects\chatbot\src\graph.py", line 136, in <module>
    _conn = psycopg.Connection.connect(_conn_string, autocommit=True)
psycopg.errors.ConnectionTimeout: connection timeout expired
Multiple connection attempts failed. All failures were:
- host: 'localhost', port: '5432', hostaddr: '::1': connection timeout expired
- host: 'localhost', port: '5432', hostaddr: '127.0.0.1': connection timeout expired

langgraph_api.utils.errors.GraphLoadError: Failed to load graph 'chat' from src.graph
```
`GraphLoadError` → starlette lifespan 예외 → 서버 종료.
`docs/langgraph-cli.md`에 적어둔 그 증상과 동일.

#### 왜 배너 뜨고 한참 뒤에 죽나
```
[error] Import for graph chat exceeded the expected startup time.
        elapsed_seconds=263.7924499999999 graph_id=chat module=src.graph
```
03:47 기동 → 03:51 사망, 약 4분. `localhost`가 `::1`과 `127.0.0.1` 두 개로 풀리는데
각각 TCP 연결 타임아웃까지 기다려서 생긴 시간임.
**즉 `langgraph dev`는 배너를 먼저 출력하고 나중에 그래프를 임포트하므로, 배너 = 정상 기동이 아님.**

### 4. → Studio `Failed to fetch`

서버가 죽었으니 포트 2024에 리스너가 없음:
```
Get-NetTCPConnection -LocalPort 2024 -State Listen   # 결과 없음
Invoke-WebRequest http://127.0.0.1:2024/ok           # 원격 서버에 연결할 수 없습니다
```
Studio는 브라우저에서 `baseUrl=http://127.0.0.1:2024`로 fetch를 시도하는데 붙을 서버가 없어서 `Failed to fetch`.
**CORS나 mixed content 문제가 아님.**

---

## 해결

`projects/chatbot`에서:
```
docker compose --env-file ../../.env -f docker/docker-compose.yaml up -d
docker ps          # 0.0.0.0:5432->5432/tcp 인지 확인
langgraph dev
```
* `--env-file` 경로는 **cwd 기준 상대경로**라서 `projects/chatbot`에서 실행할 때 `../../.env`.
* 설정이 바뀌었으므로 `up -d`가 컨테이너를 재생성함. 데이터는 `./postgres/data` 바인드 마운트라 유지됨.

### 대안
`--env-file`을 매번 붙이는 게 번거로우면 `POSTGRES_*` 네 줄만 `docker/.env`로 복사해두면 됨. 대신 비밀번호가 저장되는 곳이 한 군데 더 늘어남.

### 참고
`langgraph.json`에 `"env"` 키가 없지만, `graph.py`가 직접 `load_dotenv(find_dotenv())`를 호출하고 있어서 동작에는 문제 없음.

---

## 추가로 볼 것 (별건)

요약의 "부수적 원인" 부분. 로그가 같이 경고한 내용:
```
Import for graph chat exceeded the expected startup time.
Slow initialization (often due to work executed at import time) can delay readiness,
reduce scale-out capacity, and may cause deployments to be marked unhealthy.
```
지금은 `graph.py` 모듈 최상단(import 시점)에서 DB에 접속하고 `_checkpointer.setup()`까지 함:
```python
_conn = psycopg.Connection.connect(_conn_string, autocommit=True)
_checkpointer = PostgresSaver(_conn)
_checkpointer.setup()
graph = builder.compile(checkpointer=_checkpointer)
```
이래서 DB가 조금이라도 이상하면 **그래프 로드 자체가 실패하고 서버가 통째로 죽음**.
`langgraph dev`는 자체 체크포인터를 제공하므로, 로컬 개발에서는 Postgres 체크포인터를
빼거나 지연 연결(lazy)로 바꾸면 Docker 없이도 Studio를 띄울 수 있음. → 추후 정리

## 교훈
* Studio의 `Failed to fetch`는 대부분 **서버가 안 떠 있다는 뜻**. 브라우저/CORS부터 의심하지 말고 `http://127.0.0.1:2024/ok`부터 찍어볼 것.
* `langgraph dev`는 배너를 먼저 출력하고 나서 그래프를 임포트하므로, **배너가 떴다고 정상 기동이 아님.**
* `find_dotenv()`(상위 탐색함)와 `docker compose`(상위 탐색 안 함)의 `.env` 탐색 규칙이 다르다는 점이 이번 문제의 핵심.
