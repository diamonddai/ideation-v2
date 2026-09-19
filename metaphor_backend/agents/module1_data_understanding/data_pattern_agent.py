from pydantic import BaseModel
from fastapi import APIRouter
from typing import List, Dict, Any, Optional
import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv, find_dotenv
import re  # 在文件顶部添加



load_dotenv(find_dotenv())
router = APIRouter()

class DataInsightInput(BaseModel):
    fieldTypes: Dict[str, str]
    sampleData: List[Dict[str, Any]]
    rowNames: List[str]   # row index values
    colNames: List[str]   # column headers
    fullData: Optional[str] = None  # full dataset text (CSV)

class DataInsightOutput(BaseModel):
    dataFacts: List[str]

# =========================
# Prompt templates
# =========================

FACT_DEFINITION = """
You will discover useful insights based on the following seven categories of "data facts":
1) Trend: increasing / decreasing / stable, seasonal, or shape (e.g., "rising over time").
2) Extremum: maximum / minimum or extreme dominance.
3) Distribution: density / shape features (skewness, clustering, long-tail, concentrated or dispersed).
4) Outlier: values that deviate significantly from the majority.
5) Association: significant relationship between two measures (non-trivial, not derived).
6) Category: category structure and coverage (dominant category, categorical differences).
7) Difference: significant contrast between two groups/dimensions (higher/lower).
""".strip()

PROMPT_THEME = """
Based on the following headers and some row indices, provide a short theme of this dataset in one sentence (English only):

- Headers: {headers}
- Row indices sample: {indices}

Output only one plain English sentence, nothing else.
""".strip()

PROMPT_FACT_ONE = """
You are a rigorous data analysis expert. Based on the **entire dataset content** (truncated if too long) and the **headers**, output **exactly ONE** "data fact" that covers header keywords and is strongly related to the dataset theme.

Requirements:
- Use one concise English sentence (≤60 words), without numeric details.
- You must output one fact. Do NOT output "no valuable fact" or empty results.
- Avoid trivial or template-like descriptions (e.g., "top1 dominates", "max value is ...").
- Must reflect structural patterns across time, groups, or dimensions.
- Avoid obvious/derived relationships (e.g., A = B + C, ratio vs numerator/denominator).

Theme: {theme}
Headers: {headers}
Table text (may be truncated to {max_chars} chars, but structure preserved):
{table_text}

Return strictly in JSON format (no other content):
{{
  "dataFacts": ["one-sentence fact"]
}}
""".strip()

# =========================
# HTTP Chat call
# =========================

def _chat_raw(system: str, user: str, model: str = None, timeout: int = 120) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not detected. Please set it in .env or environment variables.")
    base = os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1").rstrip("/")
    model = model or os.getenv("OPENAI_MODEL_NAME") or "gpt-4o-mini"
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")
    try:
        j = resp.json()
    except ValueError:
        return resp.text
    if isinstance(j, dict) and j.get("choices"):
        ch0 = j["choices"][0]
        if isinstance(ch0, dict):
            msg = ch0.get("message", {}) or {}
            content = msg.get("content") or ch0.get("text")
            if content:
                return content
    for k in ("data", "result", "output", "message", "content", "text"):
        if isinstance(j, dict) and isinstance(j.get(k), str) and j[k].strip():
            return j[k]
    return json.dumps(j, ensure_ascii=False)


# 然后替换 _force_json 函数


def _force_json(text: str) -> Any:
    """
    Force JSON parsing even if model output contains code blocks or extra text.
    """
    # 移除<think></think>标签
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()
    try:
        return json.loads(t)
    except Exception:
        s = t.find("{"); e = t.rfind("}")
        if s != -1 and e != -1 and e > s:
            return json.loads(t[s:e+1])
        raise
# def _force_json(text: str) -> Any:
#     """
#     Force JSON parsing even if model output contains code blocks or extra text.
#     """
#     t = text.strip()
#     if t.startswith("```"):
#         t = t.strip("`")
#         if t.lower().startswith("json"):
#             t = t[4:].strip()
#     try:
#         return json.loads(t)
#     except Exception:
#         s = t.find("{"); e = t.rfind("}")
#         if s != -1 and e != -1 and e > s:
#             return json.loads(t[s:e+1])
#         raise

# =========================
# Utility functions
# =========================

def _is_trivial_fact(s: str) -> bool:
    s = (s or "").strip()
    if not s or len(s) < 6:
        return True
    return False

def _shrink(s: str, n: int = 60) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s[:n] if len(s) > n else s

# =========================
# Single table analysis
# =========================

def llm_infer_theme(headers: list, indices: list) -> str:
    sys = "You are a data analysis expert."
    user = PROMPT_THEME.format(headers=headers[:80], indices=indices[:30])
    return _chat_raw(sys, user).strip()

def llm_one_fact(theme: str, headers: list, table_text: str, max_chars: int = 120000) -> str:
    sys = "You are a strict data insights expert. Return strictly valid JSON."
    user = PROMPT_FACT_ONE.format(
        theme=theme,
        headers=headers[:80],
        table_text=table_text[:max_chars],
        max_chars=max_chars
    )

    # First attempt
    text = _chat_raw(sys, user)
    candidate = None
    try:
        obj = _force_json(text)
        arr = obj.get("dataFacts", [])
        if isinstance(arr, list) and arr:
            candidate = _shrink(arr[0])
    except Exception:
        candidate = None

    # Retry if result is invalid
    if not candidate or _is_trivial_fact(candidate):
        user2 = user + "\n\nNote: You must output one fact showing trend/difference/association. Empty or trivial answers are forbidden."
        text2 = _chat_raw(sys, user2)
        try:
            obj2 = _force_json(text2)
            arr2 = obj2.get("dataFacts", [])
            if isinstance(arr2, list) and arr2:
                candidate = _shrink(arr2[0])
        except Exception:
            pass

    # Fallback
    if not candidate or _is_trivial_fact(candidate):
        candidate = "The dataset shows certain trends or differences."

    return candidate

def _sample_to_csv(sample_data: list, col_names: list) -> str:
    df = pd.DataFrame(sample_data, columns=col_names)
    return df.to_csv(index=False)

@router.post("/analyze/insight", response_model=DataInsightOutput)
async def data_insight_agent(input_data: DataInsightInput) -> DataInsightOutput:
    """
    Data Insight Extraction Agent:
    - Supports input of full dataset text (fullData) or sampleData.
    - Always ensures at least one valid data fact is returned.
    """
    try:
        # Use fullData if provided
        if input_data.fullData:
            table_text = input_data.fullData
        else:
            table_text = _sample_to_csv(input_data.sampleData, input_data.colNames)
        
        # Infer theme
        theme = llm_infer_theme(input_data.colNames, input_data.rowNames)
        
        # Extract one data fact
        fact = llm_one_fact(theme, input_data.colNames, table_text)
        print("Raw LLM fact:", fact)
        return DataInsightOutput(dataFacts=[fact])
    except Exception as e:
        return DataInsightOutput(dataFacts=[f"Analysis failed: {str(e)}"])
