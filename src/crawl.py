from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# local
src_path = str(Path(__file__).parents[0])
sys.path += [src_path]
from crawl_utils import whether_to_crawl, get_classes

def get_source(url:str) -> str:
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    for trial_num in range(3):
        img_path = f"screenshot_{trial_num}.png"
        driver.save_screenshot(img_path)
        whether_to_crawl_or_not = whether_to_crawl(img_path)
        if whether_to_crawl_or_not:
            return driver.page_source
        else:
            time.sleep(3)
            continue

    driver.quit()

def get_content(source:str, instruction:str) -> dict:
    valid_tag_or_classes:list[dict] = get_classes(source=source,
                                                  instruction=instruction,
                                                  max_tokens=8000)
    soup = BeautifulSoup(source, 'html.parser')
    tags = list()
    for valid_tag_or_class in valid_tag_or_classes:
        tag = soup.find_all(**valid_tag_or_class)
        tags.append(tag)
    return tags

    
if __name__ == "__main__":
    source = get_source(url = "https://brand.naver.com/3ce/products/5333881693?NaPm=ct%3Dmgxc08x1%7Cci%3DERaf87b606%2Dacb5%2D11f0%2D9b02%2Dc299ad878aeb%7Ctr%3Dsa%7Chk%3D20d95358ce26e20755f5eb79d0667b462fe74981%7Cnacn%3DwdKfDohEGEcDB")
    tags = get_content(source=source, instruction="AI리뷰요약에 해당하는 부분을 가져와줘")
    print(tags)