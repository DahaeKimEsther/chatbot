from langchain.tools import tool
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.utils import aladin_search_api, naver_book_api
from src.tool_schema import AladinBookSearchParams, NaverBookSearchParams, KeywordAnswer
load_dotenv()

@tool(args_schema=AladinBookSearchParams)
def basic_book_search(Query:str,
                QueryType:str="Keyword",
                SearchTarget:str="Book",
                Sort:str="Accuracy"):
    """search books according to parameters

        Available Response:
        link, title, author, pubdate
        
    """
    input_params = locals()
    fixed_params = {
        "ttbkey": os.getenv("ALADIN_API_KEY"),
        "MaxResults": 10,
        "start": 1,
        "output": "xml",
    }
    params = {**input_params, **fixed_params}
    output_keys = ["link", "item.title", "item.link", "item.author", "item.pubdate"]
    result = aladin_search_api(params, output_keys)
    return result

@tool(args_schema=NaverBookSearchParams)
def price_description_book_search(query:str,
                sort:str="sim",
                d_titl:str | None = None,
                d_isbn:str | None = None):
    """search books according to parameters
    
        Available Response
        discount(lowest price of book), description
    """
    params = locals()
    result = naver_book_api(params)
    result_items = [{ k:v for k, v in item.items() if k in ["title", "discount", "description"]} for item in result["items"]]
    return result_items

@tool
def keyword_generator(search_query:str):
    """
    keyword maker to generate keywords related to question that user made so that user can get recommended books by searching keywords in book store's web page
    """
    model = ChatOpenAI(model="gpt-4o-mini")
    structured_model = model.with_structured_output(schema=KeywordAnswer)
    messages = [
        (
            "system",
            "You are keyword maker to generate keywords related to question that user made so that you can recommend books by searching keywords in book store's web page",
        ),
        ("human", search_query),
    ]
    result = structured_model.invoke(input=messages)
    return result

if __name__ == "__main__":
    # # keyword generator test
    # result = keyword_generator.invoke({"search_query": "천문학을 배우고 싶은데 어떤 책이 좋을까?"})
    # print(result)
    
    # price description test
    result = price_description_book_search.invoke({"query": "천문학"})
    print(result)