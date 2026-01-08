from pydantic import BaseModel, Field
from typing import Literal, Optional

class AladinBookSearchParams(BaseModel):
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
    
class NaverBookSearchParams(BaseModel):
    """Params for book_search"""
    query: str = Field(description="검색어")
    sort:Literal["sim", "date"] = Field("""## 정렬순서
    sim: 정확도순으로 내림차순 정렬(기본값)
    date: 출간일순으로 내림차순 정렬
    """
    )
    d_titl: Optional[str] = Field(
        default=None,
        description="검색할 책 제목"
    )
    d_isbn: Optional[str] = Field(
        default=None,
        description="검색할 ISBN"
    )

class KeywordAnswer(BaseModel):
    keywords: list[str]