


1. 가상환경 활성화
```
conda activate chatbot
```
2. 실행경로
* book_chatbot_manual 자체를 기본 workspace 경로로 가정함
* langgraph.json이 있는 경로

3. Docker(Postgres) 실행
```
docker compose --env-file ./.env -f docker/docker-compose.yaml up -d
```
* `src/book_chatbot/graph.py`에서 체크포인터가 `localhost:5432` Postgres에 연결함
* 이게 안 켜져 있으면 `langgraph dev` 실행 시 `connection timeout expired` 에러로 서버가 죽음
* `docker ps`로 `bookchatbot-postgres` 컨테이너가 떠 있는지 확인 가능

4. langgraph-cli 실행
```
langgraph dev
```
* 뒤에 `--config langgraph.json`이 생략됨