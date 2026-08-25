# pytest 실행 매뉴얼

**작성 날짜:** 2026-08-25

## 개요

`test/conftest.py`가 pytest 진입점이 되어 테스트 실행 전 `.env`를 로드합니다. 이를 통해 테스트 환경에서 OpenAI API key 등 필수 환경변수가 사용 가능합니다.

---

## 기본 사용법

### 모든 테스트 실행

```bash
pytest
```

또는 명시적으로:

```bash
pytest test/
```

**기대 결과:**
```
test/test_book_memo_agent.py .                                    [100%]

============================== 1 passed in 0.50s ==============================
```

### 상세 출력 모드 (verbose)

```bash
pytest -v
```

테스트 이름과 결과를 더 자세히 표시:
```
test/test_book_memo_agent.py::test_book_memo_agent PASSED         [100%]
```

### 특정 테스트 파일만 실행

```bash
pytest test/test_book_memo_agent.py
```

### 특정 테스트 함수만 실행

```bash
pytest test/test_book_memo_agent.py::test_book_memo_agent
```

### print() 문 출력과 함께 실행 (디버깅용)

```bash
pytest -s
```

또는 상세 + 출력:

```bash
pytest -v -s
```

테스트 코드에서 `print()`한 내용이 터미널에 표시됩니다.

---

## conftest.py 역할

`test/conftest.py`는 pytest가 테스트 모듈을 임포트하기 **전에** 실행되는 설정 파일입니다.

### 수행 작업

1. `.env` 파일 경로 확인 (프로젝트 루트)
2. `.env` 파일 없으면 `FileNotFoundError` 발생
3. `load_dotenv()`로 환경변수 로드
4. 이후 테스트 모듈의 ChatOpenAI 임포트 시 API key 사용 가능

### 경로 고정 이유

```python
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
```

- `find_dotenv()`는 상위 디렉터리를 거슬러 올라가며 찾음
- 프로젝트에 `.env`가 없으면 조용히 `workspaces/.env`를 집어옴
- 경로를 명시적으로 고정하면 상위 탐색 회피 가능

**참고:** [docs/issues/260813_langgraph-dev-postgres-port.md](issues/260813_langgraph-dev-postgres-port.md)

---

## 문제 해결

### 에러: `OpenAIError: The api_key client option must be set`

**원인:** `.env` 파일이 없거나 conftest.py가 로드되지 않음

**해결:**
1. 프로젝트 루트에 `.env` 파일 존재 확인
2. OPENAI_API_KEY 등 필수 환경변수 설정 확인
3. `pytest`를 프로젝트 루트에서 실행 확인

### 에러: `FileNotFoundError: .env를 찾을 수 없습니다`

**원인:** conftest.py가 `.env` 파일을 찾지 못함

**해결:**
프로젝트 루트 구조 확인:
```
book_chatbot_manual/
├── .env                    ← 이 위치에 있어야 함
├── test/
│   ├── conftest.py
│   └── test_*.py
├── src/
│   └── book_chatbot/
└── ...
```

---

## 환경변수 (.env) 설정

필수 환경변수 (테스트 실행 시):

```
OPENAI_API_KEY=<your-openai-api-key>
ALADIN_API_KEY=<your-aladin-api-key>
NAVER_CLIENT_ID=<naver-client-id>
NAVER_CLIENT_SECRET=<naver-client-secret>

POSTGRES_USER=bookchatbot_user
POSTGRES_PASSWORD=<password>
POSTGRES_DB=bookchatbot
POSTGRES_PORT=5432
```

**주의:** `.env`는 절대 git에 커밋하면 안 됨 (`.gitignore` 참고)

---

## CI/CD 환경에서 실행

GitHub Actions 등에서 테스트를 실행할 때는 `.env` 파일 대신 환경변수를 직접 설정:

```yaml
# .github/workflows/test.yml 예시
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      ALADIN_API_KEY: ${{ secrets.ALADIN_API_KEY }}
      # ... 기타 환경변수
    steps:
      - uses: actions/checkout@v3
      - name: Run pytest
        run: pytest -v
```

conftest.py는 `Path().exists()` 체크만 하고 파일을 반드시 읽을 필요는 없으므로, 이 방식도 고려할 수 있습니다.

---

## 참고

- pytest 공식 문서: https://docs.pytest.org/
- conftest.py 상세: https://docs.pytest.org/en/stable/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
- 최근 커밋 참고: `5dbc3ae` (`.env` 로딩을 진입점으로 이동)
