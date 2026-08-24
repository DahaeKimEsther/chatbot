## 260814

`langgraph dev`가 기동 직후 죽고 Studio에 `Failed to initialize Studio` / `Error Failed to fetch`가 뜬다.
**[260813](260813_langgraph-dev-postgres-port.md)과 증상은 같지만 원인이 다르다.** 그때는 Postgres 포트가 어긋나 연결 타임아웃으로 죽었고, 이번엔 연결이 성공한 뒤 **그 다음 단계**에서 죽는다.

---

## 요약

**`langgraph dev`는 커스텀 체크포인터를 가진 그래프를 거부한다.**

`graph.py`가 `builder.compile(checkpointer=PostgresSaver(...))`로 그래프를 만드는데,
LangGraph API(=`langgraph dev`)는 자체 persistence를 제공하므로 이걸 에러로 처리한다.

```
ValueError: Your graph 'graph' includes a custom checkpointer (PostgresSaver).
With LangGraph API, persistence is handled automatically by the platform...
→ GraphLoadError: Failed to load graph 'chat' from book_chatbot.graph
→ Application startup failed. Exiting.
```

그래프 로드 실패 → starlette lifespan 예외 → 서버 종료 → 2024 포트에 리스너 없음 → Studio `Failed to fetch`.
**마지막 인과 사슬은 260813과 완전히 동일하다.**

### 왜 이제서야 나타났나

260813에서는 `psycopg.Connection.connect()`가 타임아웃으로 죽어서, 그 아래 줄인
`builder.compile(checkpointer=...)`까지 도달하지도 못했다.
포트를 고쳐 연결이 성공하니 비로소 체크포인터 검증까지 진행됐고, 거기서 걸렸다.
**이 에러는 원래부터 포트 문제 뒤에 숨어 있었다.**

---

## 확인한 사실

| 항목 | 상태 |
|---|---|
| Postgres 컨테이너 | `Up (healthy)` / `0.0.0.0:5432->5432/tcp` — 정상 |
| 2024 포트 리스너 | **없음** — 서버가 죽었다는 뜻 |
| `http://127.0.0.1:2024/ok` | 연결 실패 |
| `import book_chatbot.graph` (.env 로드 후) | **성공** — 코드 자체는 멀쩡 |

`docker compose`는 `--env-file`을 붙여야 한다. `-f docker/docker-compose.yaml`을 주면
compose의 프로젝트 디렉터리가 `docker/`가 되어 `docker/.env`를 찾는데 거기엔 없다.

```
docker compose --env-file ./.env -f docker/docker-compose.yaml up -d
```

붙이기 전후 `docker compose config` 비교:

```
--env-file 없이            --env-file ./.env
  ports:                     ports:
    target: 5432               target: 5432
    (published 없음)  ←★       published: "5432"  ✓
```

★ `published`가 없으면 호스트 포트가 랜덤 배정된다. 260813의 51382가 이것.

---

## 충돌하는 요구

| | 체크포인터 |
|---|---|
| `langgraph dev` | 있으면 **거부** (자기가 관리) |
| `streamlit` | `thread_id` 대화 이력에 **필요** (`chat.py:34`, `chat.py:48`) |

`graph.py`가 만드는 `graph` 객체는 하나인데 두 곳에서 가져다 쓴다.
한쪽은 체크포인터가 있어야 하고 다른 쪽은 있으면 안 된다.

---

## 해결안 (아직 미적용)

**설계도(`builder`)는 하나, 거기서 그래프를 두 번 찍어낸다.**

### `src/book_chatbot/graph.py` (현재 129~137줄)

```python
# AS-IS — 모듈 최상단에서 DB 접속. 임포트만 해도 실행됨
_conn_string = (...)
_conn = psycopg.Connection.connect(_conn_string, autocommit=True)
_checkpointer = PostgresSaver(_conn)
_checkpointer.setup()
graph = builder.compile(checkpointer=_checkpointer)
```

```python
# TO-BE
graph = builder.compile()                    # 체크포인터 없음 → langgraph.json이 가리키는 것

def _conn_string() -> str:                   # 변수 -> 함수 (os.getenv도 호출 시점에)
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@localhost:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
    )

def build_graph_with_checkpointer():         # def = 부를 때만 실행 → 임포트 시 DB 안 건드림
    conn = psycopg.Connection.connect(_conn_string(), autocommit=True)
    cp = PostgresSaver(conn)
    cp.setup()
    return builder.compile(checkpointer=cp)
```

### `streamlit/chat.py` (4줄, 48줄)

```python
from book_chatbot.graph import build_graph_with_checkpointer

@st.cache_resource        # streamlit은 상호작용마다 스크립트를 재실행한다.
def _graph():             # 캐시 없으면 rerun마다 Postgres 연결이 새로 열려 쌓인다.
    return build_graph_with_checkpointer()

# 호출부: graph.invoke(...) -> _graph().invoke(...)
```

### 이 변경으로 같이 해결되는 것

- 임포트 시점에 DB를 안 건드림 → **Docker 없이도 `langgraph dev`가 뜬다**
- 260813의 `Import for graph chat exceeded the expected startup time` 경고 해소
  (260813 문서의 "추가로 볼 것"에 적어둔 그 항목)
- streamlit 체감 동작은 그대로

### 알아둘 것

체크포인터가 서로 다르므로 **Studio와 streamlit은 대화 스레드를 공유하지 않는다.**
디버깅 트래픽이 앱 DB에 섞이지 않으므로 오히려 바람직하다.

---

## 참고: 체크포인터란

그래프가 스텝마다 상태를 저장했다가 같은 `thread_id`로 오면 복원해주는 장치.
없으면 `graph.invoke()`가 매번 백지에서 시작한다.

저장 대상은 `OverallState` 전체 (`messages`, `classification`, `remaining_intents`,
`search_results`, `draft_response`).

Postgres에 실제로 생성돼 있는 테이블:

```
checkpoints            ← PostgresSaver.setup()이 만든 것
checkpoint_blobs
checkpoint_writes
checkpoint_migrations
conversations          ← streamlit/db.py가 만든 별개 테이블 (화면에 뿌릴 채팅 로그)
users
```

앞의 4개는 **그래프 내부 상태**, 뒤의 2개는 **사람이 볼 대화 기록**. 목적이 다르다.

---

## 오늘 함께 한 작업 (맥락)

이번 이슈와 별개로 진행한 것들. 새 세션에서 코드를 볼 때 필요한 배경.

### 1. `src` → 설치 가능한 `book_chatbot` 패키지 (커밋 `6243a9e`, 푸시됨)

- `src/__init__.py`가 있어 `src` 자체가 패키지였고, 그래서 임포트가 cwd에 의존했다
- `pyproject`의 `name`("chatbot")과 일치하는 패키지가 없어 빌드가 실패했다
  (`ModuleOrPackageNotFoundError: No file/folder found for package chatbot`)
- `src/*.py` → `src/book_chatbot/` (표준 src 레이아웃), 패키지 내부는 상대 임포트
- `poetry install`로 editable 설치 → `streamlit/app.py`의 `sys.path.append` 제거

### 2. `.env` 로딩을 진입점으로 (커밋 `5dbc3ae`, 푸시됨)

라이브러리(`graph.py`, `tool.py`)가 임포트 시점에 `load_dotenv()`를 부르던 것을 제거.
이제 `.env`를 읽는 곳은 진입점 세 군데뿐이고, 라이브러리는 `os.getenv()`로 읽기만 한다.

```
langgraph.json의 "env": ".env"   -> langgraph dev
streamlit/app.py                 -> streamlit run
test/conftest.py                 -> pytest
```

`.env`에서 정리한 것:
- 한글 주석 제거 (UTF-8인데 `langgraph_api`가 `DotEnv(encoding=None)`로 열어
  cp949로 디코딩 → `UnicodeDecodeError`. `load_dotenv()`는 기본이 `encoding='utf-8'`이라 안 걸렸다)
- 죽은 `PYTHONPATH="...projects/chatbot"` 제거 (옛 경로. 런타임에 설정해봐야 무의미)

### 3. pytest 도입 (커밋 `5dbc3ae`)

- pytest가 설치돼 있지 않아 `test/`가 한 번도 실행된 적이 없었다
- `poetry add --group dev pytest` → lock 변경은 4개 패키지 추가뿐, 기존 핀은 그대로
- `pytest test/` 1 passed. 다만 **저자·출판사·ISBN이 비어서 나온다** (아래 참고)

### 4. 환경 정리

- `.venv.broken-anaconda/` — 2025-10-18에 만들어진 유물. 크롤링 시절(openai+bs4+tqdm)의 venv로,
  `anaconda3` → `miniconda3` 이전으로 베이스가 사라져 깨져 있었다. 삭제함
- 삭제 후 VS Code가 그 경로를 계속 activate하려 해서 터미널에 에러가 났다
  → `Python: Select Interpreter`로 `miniconda3/envs/chatbot` 재지정 필요

---

## 현재 저장소 상태

```
5dbc3ae  refactor: load .env at entry points and add pytest      (origin/main과 동기)
6243a9e  refactor: make src an installable book_chatbot package not to use sys.path
```

**커밋 안 된 것:**

```
M  docs/langgraph-cli.md    docker compose --env-file 추가, 실행경로 설명 수정
M  pyproject.toml           [tool.poetry] packages 명시 추가
?? test/conftest.py         ← 중요
```

---

## 다음 세션에서 할 것

1. **`test/conftest.py`를 커밋한다 (최우선)**
   `5dbc3ae`에서 누락됐고 이미 푸시됐다. 지금 저장소는 테스트가 깨진 상태다 —
   `test_book_memo_agent.py`에서 `load_dotenv()`를 뺐는데 대체할 `conftest.py`가 없어서,
   새로 클론해 `pytest test/`를 돌리면 `OpenAIError: The api_key client option must be set`로 죽는다.
   히스토리 수정 없이 추가 커밋 하나면 된다.

2. **위 해결안을 적용하고 `langgraph dev`로 2024 포트가 실제로 열리는지 확인**

3. **`book_memo_agent` 결과의 빈 필드 조사**
   테스트는 통과하지만 저자·출판사·ISBN이 비어 있다. 테스트가 `title`/`pages_read`/`impression`만
   검사해서 통과한 것. 알라딘/네이버 검색 툴을 안 부르는지, 부르는데 매핑이 안 되는지 확인 필요.

4. (선택) `.gitignore`에 `.pytest_cache/`, `.venv*/` 추가
