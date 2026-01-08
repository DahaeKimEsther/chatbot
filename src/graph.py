from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command, RetryPolicy
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage

from src.schema import BookSupervisorAgentState, FeatureClassification

llm = ChatOpenAI(model="gpt-5.2")

def classify_intent(state:BookSupervisorAgentState) -> Command[Literal["book_serach", "book_recommendation", "introduce_features"]]:
    """Use LLM to classify email intent"""
    structured_llm = llm.with_structured_output(FeatureClassification)
    
    classification_prompt = f""" 
    Analyze this customer message and classify his/her last intention:

    Messages: {state['messages']}

    Provide classification including book_search, book recommendation, introduce_current_features
    and reason why you choose the classification
    """ # not stored in state
    
    classification = structured_llm.invoke(classification_prompt)
    if classification["intent"] == "book_search":
        goto = "book_search"
    elif classification["intent"] == "book_recommendation":
        goto = "book_recommendation"
    else:
        goto = "introduce_features"
        
    return Command(
        update={"classiciation":classification},
        goto=goto,
    )
    
# TODO: 의도분석 아래 sub agent에 해당하는 node 만들기
# 1. Think in LangGraph; Implementing our email agent nodes
# https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph#implementing-our-email-agent-nodes

# 2. Command
# https://docs.langchain.com/oss/python/langgraph/graph-api#command