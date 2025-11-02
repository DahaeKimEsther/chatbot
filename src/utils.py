import logging
import sys
import os
import requests
import xmltodict

class KeywordFilter(logging.Filter):
    private_token = "&&&DEBUG&&&"
    def filter(self, record):
        return self.private_token in record.getMessage()
    
class LoggingTool:
    """
    from utils import LoggingTool
    logger = LoggingTool.get_logger(__name__)
    logger.debug(f"messages")
    """
    @staticmethod
    def get_logger(name: str, setLevel=logging.INFO):
        logger = logging.getLogger(name)
        if not logger.handlers:  # 중복 핸들러 방지
            handler = logging.StreamHandler(sys.stderr)
            # stream_handler.addFilter(KeywordFilter()) # KeywordFilter.private_token을 message에 추가
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s - [%(filename)s : %(funcName)s() : %(lineno)d] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(setLevel)
        return logger
    
    @staticmethod
    def set_root_logger(setLevel=logging.INFO):
        stream_handler = logging.StreamHandler(sys.stdout)
        # stream_handler.addFilter(KeywordFilter())

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(
            level=setLevel,
            format='%(asctime)s - %(levelname)-8s - [%(filename)s : %(funcName)s() : %(lineno)d] - %(message)s',
            handlers=[stream_handler]
        )

def naver_book_api(params:dict) -> dict:
    """
    Search books according to keywords
    
    Args: 
        params (dict): parameters to get serach result
    """
    url = "https://openapi.naver.com/v1/search/book.json"
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET"),
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status() # 에러 예외처리
    return response.json()

def aladin_search_api(params:dict, output_keys:list[str]) -> dict:
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    response = requests.get(url, params=params)
    content_dict = xmltodict.parse(response.content)["object"]
    
    result = dict()
    output_keys_item = list()
    output_keys_else = list()
    
    for output_key in output_keys:
        if "item" in output_key:
            output_keys_item.append(output_key.replace("item.", ""))
        else:
            output_keys_else.append(output_key)

    for output_key in output_keys_else:
        result[output_key] = content_dict[output_key] 
    result["item"] = [
                        {
                            k: v
                            for k, v in a_dict.items()
                            if k in output_keys_item
                        }
                        for a_dict in content_dict["item"]
                    ]
    
    return result
    
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    params = {
        "ttbkey": os.getenv("ALADIN_API_KEY"),
        "Query": "떡볶이",
        "QueryType": "Title",
        "MaxResults": 10,
        "start": 1,
        "SearchTarget": "Book",
        "output": "xml",
    }
    result = aladin_search_api(params=params, output_keys=["link", "item.title", "item.author", "item.description"])
    print(result)