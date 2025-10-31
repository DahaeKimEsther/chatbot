from langchain.tools import tool
import os
import urllib.request
import requests
import xml.etree.ElementTree as ET
import re
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

def aladin_search(query:str):
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "ttbkey": os.getenv("ALADIN_API_KEY"),
        "Query": query,
        "QueryType": "Title",
        "MaxResults": 10,
        "start": 1,
        "SearchTarget": "Book",
        "output": "xml",
    }
    response = requests.get(url, params=params)
    # XML 파싱
    tree = ET.ElementTree(ET.fromstring(response.content))
    root = tree.getroot()
    namespace_uri = re.match(r"\{(.+?)\}", root.tag).group(1)
    ns = {"ns": namespace_uri} # 네임스페이스 추출
    
    for item in root.findall(f".//ns:item", ns):
        print("="*100)
        title = item.find("ns:title", ns); print(title.text)
        description = item.find("ns:description", ns); print(description.text)
        title = item.find("ns:title", ns); print(title.text)
    
if __name__ == "__main__":
    # result = naver_book(search_word="떡볶이", display=3)
    # print(result)
    
    result = aladin_search(query="떡볶이")
    print(result)