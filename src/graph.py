from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition

from src.schema import OverallState, FeatureClassification
from src.tool import basic_book_search, price_description_book_search, keyword_generator

llm = ChatOpenAI(model="gpt-5.2")
book_search_tool_node = ToolNode([basic_book_search, price_description_book_search])
book_recommendation_tool_node = ToolNode([basic_book_search, keyword_generator])

def classify_intent(state: OverallState) -> Command[Literal["book_search", "book_recommendation"]]: # , "book_recommendation", "introduce_features"]
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
    # else:
    #     goto = "introduce_features"

    return Command(
        update={
            "classification": classification,
            "messages": [HumanMessage(content=classification["query_related_to_intent"])]
            # 추후 의도가 여러 개인 요청사항이 오면 의도별로 나눠서 HummanMessage 저장
        },
        goto=goto,
    )


def book_search(state: OverallState) -> dict:
    """LLM이 어느 tool 노드로 갈지, 혹은 둘 다 갈지 결정."""
    model_with_tools = llm.bind_tools([basic_book_search, price_description_book_search])
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def book_recommendation(state: OverallState) -> dict:
    """LLM이 어느 tool 노드로 갈지, 혹은 둘 다 갈지 결정."""
    model_with_tools = llm.bind_tools([basic_book_search, keyword_generator])
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


def introduce_features(_state: OverallState) -> Command[Literal["draft_response"]]:
    return Command(update={}, goto="draft_response")


def draft_response(state: OverallState):
    response = llm.invoke([
        SystemMessage(content="You are a helpful book assistant. Answer the user's question based on the search results provided."),
        *state["messages"],  # tool 결과(ToolMessage)가 여기 있음
    ])
    return {"draft_response": response.content}


# ---- Graph ----
builder = StateGraph(OverallState)

#NODE
builder.add_node("classify_intent", classify_intent)
builder.add_node("book_search", book_search)
builder.add_node("book_search_tool_node", book_search_tool_node)
builder.add_node("book_recommendation", book_recommendation)
builder.add_node("book_recommendation_tool_node", book_recommendation_tool_node)
# builder.add_node("introduce_features", introduce_features)
builder.add_node("draft_response", draft_response)

# EDGE
builder.add_edge(START, "classify_intent")
# 1. book_search agent
builder.add_conditional_edges("book_search", tools_condition, {"tools": "book_search_tool_node", "__end__": "draft_response"})
builder.add_edge("book_search_tool_node", "book_search")
# 2. book_recommendation agent
builder.add_conditional_edges("book_recommendation", tools_condition, {"tools": "book_recommendation_tool_node", "__end__": "draft_response"})
builder.add_edge("book_recommendation_tool_node", "book_recommendation")
builder.add_edge("draft_response", END)

#GRAPH
graph = builder.compile()

###########################################
#26.03.15이후 -> introduce_features 및 독서 감상에 대한 대화 및 저장기능 추가하기