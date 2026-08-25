"""pytest 진입점에서 .env를 로드한다.

conftest.py는 pytest가 테스트 모듈을 임포트하기 **전에** 실행된다.
book_chatbot의 모듈들은 임포트 시점에 ChatOpenAI(...)를 만들기 때문에
그전에 환경변수가 올라와 있어야 한다.

경로를 고정하는 이유: find_dotenv()는 상위 디렉터리를 거슬러 올라가며 찾아서,
프로젝트에 .env가 없으면 조용히 workspaces/.env를 집어온다.
(docs/issues/260813_langgraph-dev-postgres-port.md 참고)
"""

from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

if not ENV_PATH.exists():
    raise FileNotFoundError(f".env를 찾을 수 없습니다: {ENV_PATH}")

load_dotenv(ENV_PATH)
