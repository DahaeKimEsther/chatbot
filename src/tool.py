from langchain.tools import tool
import os
import urllib.request
import requests
import chardet
import json
from dotenv import load_dotenv
load_dotenv()

def response_to_request(request:urllib.request.Request):
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        result = response_body.decode('utf-8')
        return result
    else:
        raise Exception(rescode)

# @tool
def naver_book(search_word:str, display:int=3) -> dict:
    """
    Search books according to keywords
    
    Args: 
        search_word (str): Search terms to look for
        display (str): the number of results to get from search engine
    """
    encText = urllib.parse.quote(search_word)
    url = f"https://openapi.naver.com/v1/search/book.json?query={encText}&display={display}&sort=sim"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", os.getenv('NAVER_CLIENT_ID'))
    request.add_header("X-Naver-Client-Secret", os.getenv("NAVER_CLIENT_SECRET"))
    result = response_to_request(request=request)
    return result

def isbn_search(isbn:str) -> dict:
    national_library_api_key = os.getenv("NATIONAL_LIBRARY_API_KEY")
    url = f"https://www.nl.go.kr/seoji/SearchApi.do?cert_key={national_library_api_key}&result_style=json&page_no=1&page_size=10&isbn={isbn}"
    request = urllib.request.Request(url)
    result = response_to_request(request=request)
    return result

# @tool
def get_table_of_contents(isbn:str) -> str:
    result = isbn_search(isbn)
    result = json.loads(result)
    table_of_contents_url = result["docs"][0]["BOOK_TB_CNT_URL"]
    response = requests.get(table_of_contents_url) #
    detected = chardet.detect(response.content)
    text = response.content.decode(detected['encoding'], errors='ignore')
    return text
    
if __name__ == "__main__":
    result = naver_book(search_word="떡볶이", display=3)
    print(result)
    
    table_of_contents = get_table_of_contents(isbn="9791196394509")
    print(table_of_contents)
