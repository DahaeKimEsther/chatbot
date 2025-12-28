from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool

from src.tool import basic_book_search, price_description_book_search, keyword_generator
model = ChatOpenAI(model="gpt-5.2")

BOOK_SEARCH_AGENT_PROMPT = (
    "Search books by extracting keywords from natural language. "
    "Use price_description_book_search if user mentions lowest price over all book sellers or user wants to know the content of every book. "
    "Otherwise, use basic_book_search as search engine of books"
)

BOOK_KEYWORD_RECOMMEND_AGENT_PROMPT = (
    "If user asks you to recommend books, then use keyword generator according to natural language of user and execute book search using those keywords generated"
)

book_search_agent = create_agent(
    model,
    tools=[basic_book_search, price_description_book_search], # naver_book_api
    system_prompt=BOOK_SEARCH_AGENT_PROMPT,
)

book_keyword_recommend_agent = create_agent(
    model,
    tools=[basic_book_search, keyword_generator], # naver_book_api
    system_prompt=BOOK_KEYWORD_RECOMMEND_AGENT_PROMPT,
)

@tool
def book_search(request: str) -> str:
    """
    Search books using natural language.
    
    Use this when user wants to find books according to title, author, publisher, lowest price or to find books by sorting books by accuracy, publish time, title, amount of sales, customer ratings and number of reivews
    
    Input: Natural language request searching books
    """
    result = book_search_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def book_recommendation(request: str) -> str:
    """
    Recommend books using natural language.
    
    Use this when user wants a list of recommended books according to user query
    
    Input: Natural language request to recommend books
    """
    result = book_keyword_recommend_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

SUPERVISOR_PROMPT = (
    "You are a helpful book assistant. "
    "You can search books or recommend books according to user request"
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

supervisor_agent = create_agent(
    model,
    tools=[book_search, book_recommendation],
    system_prompt=SUPERVISOR_PROMPT,
)

if __name__ == "__main__":
    # book_keyword_recommend_agent
    query = "천문학 입문서를 추천해줘, 그리고 히가시노 게이고의 용의자X의 헌신의 최저가를 알려줘"
    for step in supervisor_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()