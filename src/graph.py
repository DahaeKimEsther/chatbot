from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition

from src.schema import OverallState, FeatureClassification
from src.tool import basic_book_search, price_description_book_search

llm = ChatOpenAI(model="gpt-5.2")
book_search_tool_node = ToolNode([basic_book_search, price_description_book_search])

def classify_intent(state: OverallState) -> Command[Literal["book_search"]]: # , "book_recommendation", "introduce_features"]
    """Use LLM to classify book search intent"""
    structured_llm = llm.with_structured_output(FeatureClassification)

    classification_prompt = f"""
    Analyze this customer message and classify his/her last intention:

    Messages: {state['messages']}

    Provide classification including book_search, book_recommendation, introduce_current_features
    and reason why you choose the classification
    """  # not stored in state

    classification = structured_llm.invoke(classification_prompt)
    if classification["intent"] == "book_search":
        goto = "book_search"
    # elif classification["intent"] == "book_recommendation":
    #     goto = "book_recommendation"
    # else:
    #     goto = "introduce_features"

    return Command(
        update={
            "classification": classification,
            "messages": [HumanMessage(content=classification["query_related_to_intent"])]
        },
        goto=goto,
    )


def book_search(state: OverallState) -> dict:
    """LLM이 어느 tool 노드로 갈지, 혹은 둘 다 갈지 결정."""
    model_with_tools = llm.bind_tools([basic_book_search, price_description_book_search])
    
    query = state['classification']['query_related_to_intent']
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# TODO: 구현 필요
def book_recommendation(_state: OverallState) -> Command[Literal["draft_response"]]:
    return Command(update={}, goto="draft_response")


def introduce_features(_state: OverallState) -> Command[Literal["draft_response"]]:
    return Command(update={}, goto="draft_response")


def draft_response(state: OverallState):
    response = llm.invoke([
        SystemMessage(content="You are a helpful book assistant. Answer the user's question based on the search results provided."),
        *state["messages"],  # tool 결과(ToolMessage)가 여기 있음
    ])
    return {"draft_response": response.content}


# ---- Graph 조립 ----
builder = StateGraph(OverallState)

builder.add_node("classify_intent", classify_intent)
builder.add_node("book_search", book_search)
builder.add_node("book_search_tool_node", book_search_tool_node)
# builder.add_node("book_recommendation", book_recommendation)
# builder.add_node("introduce_features", introduce_features)
builder.add_node("draft_response", draft_response)

builder.add_edge(START, "classify_intent")
builder.add_conditional_edges("book_search", tools_condition, {"tools": "book_search_tool_node", END: "draft_response"})
builder.add_edge("book_search_tool_node", "book_search")
builder.add_edge("draft_response", END)

graph = builder.compile()

if __name__ == "__main__":
    from PIL import Image
    import io
    image_bytes = graph.get_graph().draw_mermaid_png()
    Image.open(io.BytesIO(image_bytes)).show()
