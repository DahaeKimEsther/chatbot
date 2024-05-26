from selenium import webdriver
from selenium.webdriver.common.by import By

class YouthCenter:
    def __init__(self) -> None:
        pass

    def get_page_content(self, current_page_url:str) -> dict:
        """_summary_

        Args:
            current_page_url (str): 한 상세페이지의 url 입력

        Returns:
            dict: 상세페이지 내 정보를 딕셔너리로 저장함.
        """
        
        with webdriver.Chrome() as driver:
            driver.get(current_page_url)
            driver.implicitly_wait(0.5)
            
            # 상세페이지 내 표제목과 표를 가져옴
            whole_header:list = driver.find_elements(by=By.CLASS_NAME, value="tbl-header")
            whole_table:list = driver.find_elements(by=By.CLASS_NAME, value="table_wrap")

            # 표 별 json 형태를 가공
            whole_document = dict()
            for a_header, a_table in zip(whole_header, whole_table):
                    
                whole_tit:list = a_table.find_elements(by=By.CLASS_NAME, value="list_tit")
                whole_cont:list = a_table.find_elements(by=By.CLASS_NAME, value="list_cont")
                table_processed:dict = {a_tit.text: a_cont.text for a_tit, a_cont in zip(whole_tit, whole_cont)}
                whole_document[a_header.text] = table_processed
            
        return whole_document
    
    def get_whole_document(self, search_result_url:str) -> list[dict]:
        """_summary_

        Args:
            search_result_url (str): 청년정책 통합검색결과 페이지 url 입력

        Returns:
            list[dict]: 상세페이지 내 정보를 딕셔너리로 저장함. 여러 상세페이지를 동일한 방식으로 저장하여 리스트에 보관.
        """
        with webdriver.Chrome() as driver:
            driver.get(search_result_url)
            driver.implicitly_wait(0.5)
            
            whole_pages = driver.find_element(by=By.CLASS_NAME, value="result-list")
            page_list:list = whole_pages.find_elements(by=By.CLASS_NAME, value='result-card-box')
            whole_document = list()
            
            for idx in range(len(page_list)):

                if idx == 0:
                    pass
                else:
                    whole_pages = driver.find_element(by=By.CLASS_NAME, value="result-list")
                    page_list:list = whole_pages.find_elements(by=By.CLASS_NAME, value='result-card-box')
                    
                status_element = page_list[idx].find_element(by=By.CLASS_NAME, value='badge').text.split('\n')[0]
                if status_element == '신청 마감':
                    pass
                else:
                    page_title = page_list[idx].find_element(by=By.CLASS_NAME, value='tit-wrap')
                    page_title.click() # 하나의 상세페이지 접속
                    page_url = driver.current_url
                    page:dict = self.get_page_content(page_url) # 하나의 상세페이지를 새로 띄워 크롤링
                    whole_document.append(page)
                    driver.back() #  검색결과 페이지로 돌아감
                    
            return whole_document