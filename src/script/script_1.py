from src.tool import book_search
from langchain.agents import create_agent
from src.utils import LoggingTool
LoggingTool.set_root_logger()

tools = [book_search]
agent = create_agent("gpt-4.1", tools=tools)

for chunk in agent.stream({
    "messages": [{"role": "user", "content": "히가시노 게이고의 신간도서가 중고로도 있어?"}]
}, stream_mode="updates"):
    for step, data in chunk.items():
        print(f"step: {step}")
        print(f"content: {data["messages"][-1].content_blocks}")
        
        # tool call id test
        print("RESPONSE_METADATA: ", data["messages"][-1].response_metadata)
        if "tool_call_id" in data["messages"][-1].response_metadata:
            print("TOOL_CALL_ID: ", data["messages"][-1].response_metadata["tool_call_id"])