from src.tool import book_params
from langchain.agents import create_agent

tools = [book_params]
agent = create_agent("gpt-4.1", tools=tools)

queries = [
    "한강 작가 도서 중에 2025년 이전에 발간된 책 하나만 말해줘",
    # "",
]

for query in queries:
    for chunk in agent.stream({
        "messages": [{"role": "user", "content": query}]
    }, stream_mode="updates"):
        for step, data in chunk.items():
            print(f"step: {step}")
            print(f"content: {data["messages"][-1].content_blocks}")
        