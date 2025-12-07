from pydantic import BaseModel, Field
from typing import Literal
from langchain.tools import tool
import os
from dotenv import load_dotenv

from src.utils import aladin_search_api
load_dotenv()

class BookSearchParams(BaseModel):
    """Params for book_search"""
    Query: str = Field(description="검색어")
    QueryType: Literal["Keyword", "Title", "Author", "Publisher"] = Field(
        default="Keyword",
        description="""##검색방식의 유형
        Keyword (기본값) : 제목+저자
        Title : 제목검색
        Author : 저자검색
        Publisher : 출판사검색
        """
    )
    SearchTarget:Literal["Book", "Used"] = Field(
        default="Book",
        description="""##쿼리를 검색할 mall
        Book (기본값): 도서
        Used : 중고샵(도서/음반/DVD 등)
        """
    )
    Sort:Literal["Accuracy", "PublishTime", "Title", "SalesPoint", "CustomerRating", "MyReviewCount"] = Field("""## 정렬순서
    Accuracy(기본값): 관련도
    PublishTime : 출간일
    Title : 제목
    SalesPoint : 판매량
    CustomerRating 고객평점
    MyReviewCount :마이리뷰갯수
    """
    )
    
class BookSearch(BaseModel):
    """input of book_search"""
    params: dict = Field(description="parameters from book_params")

@tool(args_schema=BookSearchParams)
def book_search(Query:str,
                QueryType:str="Keyword",
                SearchTarget:str="Book",
                Sort:str="Accuracy"):
    """search books according to parameters
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