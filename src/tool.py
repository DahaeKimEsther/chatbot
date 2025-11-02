from langchain.tools import tool
import os
from dotenv import load_dotenv

from src.utils import aladin_search_api
load_dotenv()

@tool
def book_title_info(title:str):
    """Search a book by title

    Args:
        title (str): search titles to look for
    """
    params = {
        "ttbkey": os.getenv("ALADIN_API_KEY"),
        "Query": title,
        "QueryType": "Title",
        "MaxResults": 10,
        "start": 1,
        "SearchTarget": "Book",
        "output": "xml",
    }
    output_keys = ["link", "item.title", "item.link", "item.author", "item.pubdate"]
    result = aladin_search_api(params, output_keys)
    return result

def book_author_info(author:str):
    """Search a book by author matching the query

    Args:
        author (str): search authors to look for
    """
    params = {
        "ttbkey": os.getenv("ALADIN_API_KEY"),
        "Query": author,
        "QueryType": "Author",
        "MaxResults": 10,
        "start": 1,
        "SearchTarget": "Book",
        "output": "xml",
    }
    output_keys = ["link", "item.title", "item.link", "item.author", "item.pubdate"]
    result = aladin_search_api(params, output_keys)
    return result