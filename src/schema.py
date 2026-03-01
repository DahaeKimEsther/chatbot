import operator
from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel
from langgraph.graph.message import add_messages

class FeatureClassification(TypedDict):
    intent: Literal["book_search", "book_recommendation", "introduce_current_features"]
    query_related_to_intent: str

# class RequestState(TypedDict):
#     user_request:str
#     status:Literal["Done", "On-going", "Pending", "End"]
#     classification_result:str
#     info:str

class OverallState(TypedDict):
    messages: Annotated[list, add_messages]  # add_messages로 ToolNode 결과 자동 축적
    classification: FeatureClassification | None # TODO(장기): list[FeatureClassification]으로 parallel하고 싶음
    search_results: Annotated[list[dict], operator.add]
    draft_response: str | None
    

class ToolRouting(BaseModel):
    tools: list[Literal["basic_book_search", "price_description_book_search"]]
    reason: str