from langchain.tools import tool
import os
import urllib.request
from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv('NAVER_CLIENT_ID')
client_secret = os.getenv("NAVER_CLIENT_SECRET")

# @tool
def naver_book(search_word:str, display:int=3) -> dict:
    """
    Search books according to keywords
    
    Args: 
        search_word (str): Search terms to look for
        display (str): the number of results to get from search engine
    """
    encText = urllib.parse.quote(search_word)
    url = "https://openapi.naver.com/v1/search/book.json?query=" + encText + f"&display={display}&sort=sim"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id",client_id)
    request.add_header("X-Naver-Client-Secret",client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        result = response_body.decode('utf-8')
        return result
    else:
        raise Exception(rescode)
    
if __name__ == "__main__":
    result = naver_book(search_word="떡볶이", display=3)
    print(result)