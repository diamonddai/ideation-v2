"""
Agent5：数据事实融合改写 Agent
根据 dataFact 特征，增强 keyword 的表达，但不改变 field 与 dataFact 本身。
要求输出 keyword 为「英文单数名词」。
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter
from typing import List, Dict, Any
import json
import re  # 添加这个导入

# 导入工具类和常量
from utils.langchain_utils import create_chain
from .constants import GUIDED, BLIND

router = APIRouter()

def clean_json_response(text: str) -> dict:
    """清理LLM响应并解析JSON"""
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

class MetaphorVariation(BaseModel):
    field: str
    keyword: str
    dataFact: str
    method: int = Field(description="0=BLIND, 1=GUIDED")

class FeatureRewriteInput(BaseModel):
    variations: List[MetaphorVariation]

class FeatureRewriteOutput(BaseModel):
    enhancedVariations: List[MetaphorVariation]

@router.post("/rewrite/feature", response_model=FeatureRewriteOutput)
async def feature_rewrite_agent(input_data: FeatureRewriteInput) -> FeatureRewriteOutput:
    """
    数据事实融合改写 Agent：
    - 作用：根据 dataFact 特征增强 keyword，但不改变 field 与 dataFact；强调输出 keyword 为英文单数名词
    - 输入：隐喻变体列表（field、keyword、dataFact、method）
    - 输出：增强后的隐喻变体列表（保持 field、dataFact、method 不变）
    """
    try:
        # 构造英文 Prompt，严格约束输入输出与风格
        prompt_template = (
            "You are a Metaphor Feature Rewriter.\n"
            "Goal: Integrate the essence of the data fact into the metaphor keyword,\n"
            "while keeping the field and the data fact unchanged.\n"
            "Rules:\n"
            "- Output 'keyword' MUST be an English common noun in singular form.\n"
            "- No adjectives, no phrases, no hyphens, no punctuation, no numbers.\n"
            "- If the current keyword already reflects the data fact, keep it as-is.\n"
            "- Otherwise, replace it with a better single-noun metaphor that reflects the data fact.\n"
            "- Do NOT change 'field', 'dataFact', or 'method'.\n"
            "- All inputs and outputs are English single nouns for 'keyword'.\n"
            "Input JSON schema:\n"
            "{\n  \"variations\": [\n    {\n      \"field\": \"string\",\n      \"keyword\": \"string\",\n      \"dataFact\": \"string\",\n      \"method\": 0 or 1\n    }\n  ]\n}\n"
            "Output JSON schema:\n"
            "{\n  \"enhancedVariations\": [\n    {\n      \"field\": \"string\",\n      \"keyword\": \"single_noun\",\n      \"dataFact\": \"string\",\n      \"method\": 0 or 1\n    }\n  ]\n}\n"
            "Now rewrite strictly and ONLY return the output JSON.\n"
        )

        chain = create_chain(prompt_template)

        # 结构化输入：直接传 JSON，以减少模型偏差
        input_payload = {
            "variations": [
                {
                    "field": v.field,
                    "keyword": v.keyword,
                    "dataFact": v.dataFact,
                    "method": v.method,
                }
                for v in input_data.variations
            ]
        }

        # 执行 LLM
        result = chain.run(variations=json.dumps(input_payload["variations"], ensure_ascii=False))

        # 解析 JSON，若失败则回退
        try:
            # parsed_result = json.loads(result)
            # 🔧 修改点：使用清理函数而不是直接json.loads
            parsed_result = clean_json_response(result)
            items = parsed_result.get("enhancedVariations", [])

            def normalize_keyword_to_single_noun(word: str) -> str:
                # 简单规则：
                # 1) 去除首尾空白与标点；2) 截断空格保留首词；3) 去除连字符；4) 去复数尾缀 s/es；
                # 该校正规则仅作兜底保护，首要依赖模型输出遵循规则。
                if not isinstance(word, str):
                    return ""
                w = word.strip().lower()
                for ch in [",", ".", "!", "?", ";", ":", "'", '"']:
                    w = w.replace(ch, "")
                w = w.split()[0] if w.split() else w
                w = w.replace("-", "")
                # 非严格的英语单数化：常见复数后缀处理
                if len(w) > 3 and w.endswith("ies"):
                    w = w[:-3] + "y"
                elif len(w) > 2 and w.endswith("es"):
                    w = w[:-2]
                elif len(w) > 1 and w.endswith("s"):
                    w = w[:-1]
                return w

            enhanced_variations: List[MetaphorVariation] = []
            for item in items:
                try:
                    field_val = item.get("field")
                    keyword_val = normalize_keyword_to_single_noun(item.get("keyword", ""))
                    data_fact_val = item.get("dataFact")
                    method_val = item.get("method")

                    # 兜底校验：缺失或关键字异常则回退原值
                    matched = next((v for v in input_data.variations if v.field == field_val and v.dataFact == data_fact_val and v.method == method_val), None)
                    if not matched:
                        continue
                    if not keyword_val:
                        keyword_val = matched.keyword

                    enhanced_variations.append(
                        MetaphorVariation(
                            field=field_val,
                            keyword=keyword_val,
                            dataFact=data_fact_val,
                            method=method_val,
                        )
                    )
                except Exception:
                    # 局部失败：跳过该项
                    continue

            # 若模型未返回有效项，则回退输入
            if not enhanced_variations:
                return FeatureRewriteOutput(enhancedVariations=input_data.variations)

            return FeatureRewriteOutput(enhancedVariations=enhanced_variations)
        except json.JSONDecodeError:
            return FeatureRewriteOutput(enhancedVariations=input_data.variations)
            
    except Exception as e:
        # 错误处理，返回原样
        return FeatureRewriteOutput(enhancedVariations=input_data.variations)