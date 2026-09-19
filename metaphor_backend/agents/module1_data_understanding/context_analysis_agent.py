from pydantic import BaseModel 
from fastapi import APIRouter
from typing import List
import json
# 修改点
import re
import os

# Import utility modules
from utils.cache_utils import cache

router = APIRouter()

class FusionUnderstandingInput(BaseModel):
    rowNames: List[str]  # original dataset row names (English),
    semanticFields: List[str] 
    dataFacts: List[str]

class BoundField(BaseModel):
    field: str
    dataFact: str
    dimensions: List[str]  # must strictly come from original column names

class FusionUnderstandingOutput(BaseModel):
    boundFields: List[BoundField]
    contextDescription: str
#修改点
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

def llm_generate(prompt: str, system_prompt: str) -> str:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    chat = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    response = chat.invoke(messages)
    return response.content.strip()

@router.post("/analyze/fusion", response_model=FusionUnderstandingOutput)
async def fusion_understanding_agent(input_data: FusionUnderstandingInput) -> FusionUnderstandingOutput:
    """
    Data-Semantic Fusion Agent:
    - Combines semanticFields (original headers) and dataFacts to generate interpretive bindings.
    """
    try:
        semantic_fields = [s for s in (input_data.semanticFields or []) if str(s).strip()]
        fact_texts = [s for s in (input_data.dataFacts or []) if str(s).strip()]
        row_names = [s for s in (input_data.rowNames or []) if str(s).strip()]
        prompt_template = """
You are given the following inputs:
- semanticFields: original dataset column names (English).
- dataFacts: extracted data facts.

Task:
1. Use semanticFields as references to form abstract fields (field can be thematic, but do not confuse with column names).
2. For each field, assign its most relevant short data fact (dataFact).
   - Only describe the phenomenon in the data.
   - Do not write inferences, causes, or implications.
   - Must be within 20 English words.
3. For each data fact, annotate two supporting dataset dimensions (dimensions).
   - ✅ dimensions must strictly be selected from the following list:
     {rowNames}
   - MUST list EXACTLY TWO dimensions, not one, not three
   - Copy column names EXACTLY as they appear (including special characters like $)
   - Do not generate new fields or translate them.
   - If multiple columns are involved, list the most relevant two of them.
4. Provide a concise contextDescription summarizing the dataset (≤30 English words).

[STRICT REQUIREMENTS]
- Return strictly in JSON format with "boundFields" and "contextDescription".
- boundFields must be an array of objects with "field", "dataFact", and "dimensions".
- dimensions must be a string array, and each value must come from {rowNames}.
- Do not output anything other than valid JSON.

[INPUT]
semanticFields: {semanticFields}
dataFacts: {dataFacts}
Available columns for dimensions: {rowNames}
"""

        prompt = prompt_template.format(
            semanticFields=semantic_fields,
            dataFacts=fact_texts,
            rowNames=row_names
        )
        system_prompt = "You are a data semantics fusion expert. Return strictly valid JSON."

        result = llm_generate(prompt, system_prompt)
        print("Raw LLM response:", result)

        # 修改点：使用内联的清理函数
        try:
            parsed = clean_json_response(result)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw response: {result}")
            return FusionUnderstandingOutput(
                boundFields=[],
                contextDescription="Failed to parse analysis results"
            )

        raw_items = parsed.get("boundFields", []) or []
        context_description = parsed.get("contextDescription", "").strip()

        valid_cols = set(row_names)
        print(f"📋 有效列名集合: {valid_cols}")
        bound: List[BoundField] = []
        for it in raw_items:
            if isinstance(it, dict) and "field" in it and "dataFact" in it:
                dims = it.get("dimensions", [])
                if not isinstance(dims, list):
                    dims = [str(dims)]
                dims = [d for d in dims if d in valid_cols]
                bound.append(BoundField(field=it["field"], dataFact=it["dataFact"], dimensions=dims))

        return FusionUnderstandingOutput(
            boundFields=bound,
            contextDescription=context_description or "Dataset characteristics not provided"
        )

    except Exception as e:
        error_context = f"Analysis failed: {str(e)}"
        print("Error:", error_context)
        return FusionUnderstandingOutput(boundFields=[], contextDescription=error_context)