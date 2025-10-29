from bs4 import BeautifulSoup
from openai import OpenAI
import base64
import tiktoken
from pydantic import BaseModel, Field
import json

#local
from src.utils import LoggingTool
logger = LoggingTool.get_logger(__name__)

client = OpenAI()
model = "gpt-4o-2024-08-06"

def encode_image(image_path:str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def whether_to_crawl(image_path:str):
    base64_image = encode_image(image_path)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": "if page is loaded and be ready to crawl say 'true' or say 'false'" },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )
    
    if response.output_text.lower() == "true":
        bool_response = True
    elif response.output_text.lower() == "false":
        bool_response = False
        
    logger.info(f"whether_to_crawl = {bool_response}")
    return bool_response

class TagClass(BaseModel):
    name: str = Field(description="the name of tag in html source")
    class_: str = Field(description="the name of class in html source")

def class_from_instruction(source:str, instruction:str) -> dict:
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": "# return tag or class in html SOURCE according to INSTRUCTION below follwing the FORMAT"},
            {
                "role": "user",
                "content": """
                ## INSTRUCTION:
                {instruction}
                
                ## SOURCE:
                {source}
                
                ## requirements
                - follow the json format: put  in 'name' and the name of class in 'class_'
                - if there is no appropriate value for json, just leave it ""(blank string)
                - if you're hesitate to put value, just leave it ""(blank string)
                """,
            },
        ],
        text_format=TagClass,
    )
    logger.info(f"response.output_text: {response.output_text}")
    if response.output_text:
        response_dict = json.loads(response.output_text)
    else:
        response_dict = {"name": "", "class_": ""}
    
    return response_dict

def get_token_count(text: str, model=model):
    """토큰 수 계산"""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def trim_source(source:str, max_tokens:int) -> list[list[str]]:
    soup = BeautifulSoup(source, 'html.parser')
    total_sections = list()
    sections = list()
    token_num = 0
    
    for tag in soup.find_all(lambda tag: tag.string and "리뷰" in tag.string):
        token_count = get_token_count(str(tag))
        if (token_num + token_count) > max_tokens:
            total_sections.append("\n\n".join(sections))
            sections = list()
            token_num = 0
        else:
            sections += [str(tag)]
            token_num += token_count
    total_sections.append("\n\n".join(sections))
    return total_sections

def get_classes(source:str, instruction:str, max_tokens:int) -> list[dict]:
    total_sections = trim_source(source=source, max_tokens=max_tokens)
    
    valid_tag_or_classes = list()
    for sections_joined in total_sections:
        tag_or_class:dict = class_from_instruction(source=sections_joined, instruction=instruction)
        valid_tag_or_class = {k:v for k, v in tag_or_class.items() if v}
        if valid_tag_or_class:
            valid_tag_or_classes.append(valid_tag_or_class)
            
    return valid_tag_or_classes