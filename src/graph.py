from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.schema import OverallState, FeatureClassification, ToolRouting
from src.tool import basic_book_search, price_description_book_search
from src.tool_schema import AladinBookSearchParams, NaverBookSearchParams

llm = ChatOpenAI(model="gpt-5.2")

def classify_intent(state: OverallState) -> Command[Literal["book_search", "book_recommendation", "introduce_features"]]:
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
    elif classification["intent"] == "book_recommendation":
        goto = "book_recommendation"
    else:
        goto = "introduce_features"

    return Command(
        update={"classification": classification},
        goto=goto,
    )


def book_search(state: OverallState) -> Command[Literal["basic_book_search", "price_description_book_search"]]:
    """LLM이 어느 tool 노드로 갈지, 혹은 둘 다 갈지 결정."""
    structured_llm = llm.with_structured_output(ToolRouting)
    query = state['classification']['query_related_to_intent']

    routing = structured_llm.invoke([
        SystemMessage(content=(
            "Decide which search tool(s) to use:\n"
            "- basic_book_search: general book info (title, author, rating, etc.)\n"
            "- price_description_book_search: lowest price or book description needed\n"
            "You can choose one or both."
        )),
        HumanMessage(content=query),
    ]) # routing 출력값 schema: ToolRouting

    if len(routing.tools) == 1:
        return Command(goto=routing.tools[0])

    # 둘 다 선택된 경우 → 병렬 실행
    return Command(goto=[Send(tool, state) for tool in routing.tools])


def run_basic_book_search(state: OverallState) -> Command[Literal["draft_response"]]:
    structured_llm = llm.with_structured_output(AladinBookSearchParams)
    query = state['classification']['query_related_to_intent']

    params = structured_llm.invoke([
        SystemMessage(content="Extract Aladin book search parameters from the user query."),
        HumanMessage(content=query),
    ])

    result = basic_book_search.invoke(params.model_dump())
    return Command(
        update={"search_results": [{"tool": "basic_book_search", "data": result}]},
        goto="draft_response",
    )


def run_price_description_book_search(state: OverallState) -> Command[Literal["draft_response"]]:
    structured_llm = llm.with_structured_output(NaverBookSearchParams)
    query = state['classification']['query_related_to_intent']

    params = structured_llm.invoke([
        SystemMessage(content="Extract Naver book search parameters from the user query."),
        HumanMessage(content=query),
    ])

    result = price_description_book_search.invoke(params.model_dump())
    return Command(
        update={"search_results": [{"tool": "price_description_book_search", "data": result}]},
        goto="draft_response",
    )


# TODO: 구현 필요
def book_recommendation(_state: OverallState) -> Command[Literal["draft_response"]]:
    return Command(update={}, goto="draft_response")


def introduce_features(_state: OverallState) -> Command[Literal["draft_response"]]:
    return Command(update={}, goto="draft_response")


def draft_response(state: OverallState):
    query = state['classification']['query_related_to_intent']
    search_results = state.get('search_results', [])

    response = llm.invoke([
        SystemMessage(content="You are a helpful book assistant. Answer the user's question based on the search results provided."),
        HumanMessage(content=f"User query: {query}\n\nSearch results: {search_results}"),
    ])

    return {"draft_response": response.content}


# ---- Graph 조립 ----
builder = StateGraph(OverallState)

builder.add_node("classify_intent", classify_intent)
builder.add_node("book_search", book_search)
builder.add_node("basic_book_search", run_basic_book_search)
builder.add_node("price_description_book_search", run_price_description_book_search)
builder.add_node("book_recommendation", book_recommendation)
builder.add_node("introduce_features", introduce_features)
builder.add_node("draft_response", draft_response)

builder.add_edge(START, "classify_intent")
builder.add_edge("draft_response", END)

graph = builder.compile()

if __name__ == "__main__":
    from PIL import Image
    import io
    image_bytes = graph.get_graph().draw_mermaid_png()
    Image.open(io.BytesIO(image_bytes)).show()
