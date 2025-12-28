from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

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

if __name__ == "__main__":
    # book_keyword_recommend_agent
    query = "천문학 입문서를 추천해줘"
    for step in book_keyword_recommend_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
    
    # # book_search_agent
    # query = "히가시노 게이고의 용의자X의 헌신의 최저가를 알려줘"
    # for step in book_search_agent.stream(
    #     {"messages": [{"role": "user", "content": query}]}
    # ):
    #     for update in step.values():
    #         for message in update.get("messages", []):
    #             message.pretty_print()