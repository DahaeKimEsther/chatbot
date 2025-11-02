from src.tool import book_title_info, book_author_info
from langchain.agents import create_agent



tools = [book_title_info, book_author_info]

agent = create_agent("gpt-4.1", tools=tools)

for chunk in agent.stream({
    "messages": [{"role": "user", "content": "'자존감'이 들어간 책들 중에서 '너새니얼 브랜든'의 책을 찾아주고, 너새니얼 브랜든의 다른 책들도 알려줘"}]
}, stream_mode="updates"):
    for step, data in chunk.items():
        print(f"step: {step}")
        print(f"content: {data['messages'][-1].content_blocks}")