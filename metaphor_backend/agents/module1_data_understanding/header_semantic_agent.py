from pydantic import BaseModel
from fastapi import APIRouter
from typing import List
import json
import re
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os

router = APIRouter()

class HeaderSemanticInput(BaseModel):
    headers: List[str]

class HeaderSemanticOutput(BaseModel):
    semanticKeywords: List[str]
    contextDescription: str

def clean_json_response(text: str) -> dict:
    """清理LLM响应并解析JSON（内联版本）"""
    # 移除<think></think>标签
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    
    # 处理markdown代码块
    if '```json' in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    elif '```' in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    
    # 找到JSON边界
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]
    
    return json.loads(text)

def llm_generate(prompt: str) -> str:
    """
    Helper function to call the LLM with a system and user prompt.
    """
    chat = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
    )
    messages = [
        SystemMessage(content="You are a data semantics expert. Generate structured results based on the user input."),
        HumanMessage(content=prompt)
    ]
    response = chat.invoke(messages)
    return response.content.strip()

@router.post("/analyze/header", response_model=HeaderSemanticOutput)
async def header_semantic_agent(input_data: HeaderSemanticInput) -> HeaderSemanticOutput:
    """
    Header Semantic Analysis Agent:
    - Goal: Infer dataset semantics using only column headers.
    - Input: list of column names.
    - Output: 3–5 representative keywords + a concise context description.
    """
    try:
        # Prompt template
        prompt_template = """
Based on the following column headers, infer the dataset's potential theme and content. Then, list 3–5 representative source keywords.

Column headers: {headers}

Return strictly in JSON format:
{{
  "semanticKeywords": ["keyword1", "keyword2", "keyword3"],
  "contextDescription": "This dataset likely concerns ..."
}}

Requirements:
1. semanticKeywords should be 3–5 English noun keywords that best represent dataset features.
2. contextDescription should briefly describe the dataset's business background and theme.
3. Keywords must be concrete nouns to support later metaphor generation.
"""
        prompt = prompt_template.format(headers=input_data.headers)
        
        # Call LLM
        try:
            result = llm_generate(prompt)
        except Exception as api_err:
            print("API call failed:", api_err)
            return HeaderSemanticOutput(
                semanticKeywords=[],
                contextDescription=f"API call failed: {str(api_err)}"
            )
        
        # Parse JSON result
        try:
            print("Raw LLM response:", result)
            parsed_result = clean_json_response(result)
            semanticKeywords = parsed_result.get("semanticKeywords", [])
            print("Parsed keywords:", semanticKeywords)
            
            return HeaderSemanticOutput(
                semanticKeywords=semanticKeywords,
                contextDescription=parsed_result.get("contextDescription", "")
            )
        except json.JSONDecodeError as fmt_err:
            print("JSON parsing failed:", fmt_err)
            print("Raw content:", result)
            return HeaderSemanticOutput(
                semanticKeywords=[],
                contextDescription="Analysis completed but result format was invalid."
            )
        
    except Exception as e:
        return HeaderSemanticOutput(
            semanticKeywords=[],
            contextDescription=f"Analysis failed: {str(e)}"
        )