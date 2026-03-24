import sys
import json
from pathlib import Path
import chainlit as cl
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

src_path = str(Path(__file__).parents[1])
sys.path += [src_path] # chatbot
from src.graph import graph


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    except TypeError:
        return str(value)


def _extract_step_content(node: str, data: dict) -> str | None:
    return _stringify(data)


@cl.on_message
async def on_message(msg: cl.Message):
    config = {"configurable": {"thread_id": cl.context.session.id}}
    final_answer = cl.Message(content="")

    for chunk in graph.stream(
        {"messages": [HumanMessage(content=msg.content)]},
        stream_mode="updates",
        config=RunnableConfig(**config),
    ):
        for node, data in chunk.items():
            if node == "draft_response" and data.get("draft_response"):
                final_answer.content = data["draft_response"]
                continue

            step_content = _extract_step_content(node, data)
            if not step_content:
                continue

            async with cl.Step(name=node, type="tool") as step:
                step.output = step_content

    await final_answer.send()
