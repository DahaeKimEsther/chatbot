from typing import TypedDict, Literal

class FeatureClassification(TypedDict):
    intent: Literal["book_search", "book recommendation", "introduce_current_features"]
    reason_choosing_the_intent: str
    
# class RequestState(TypedDict):
#     user_request:str
#     status:Literal["Done", "On-going", "Pending", "End"]
#     classification_result:str
#     info:str
    
class BookSupervisorAgentState(TypedDict):
    # request:list[RequestState]
    classification: FeatureClassification | None
    
    search_results:list[dict] | None
    user_history: str | None #chat history
    
    draft_repsonse:str | None
    messages: list[str] | None
    
# Think in LangGraph; Let’s define our state
# https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph#keep-state-raw,-format-prompts-on-demand