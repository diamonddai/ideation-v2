import os
from typing import Dict, Any, List

import os
from utils.langchain_utils import create_llm
from experiment.design_agent7_prompt.prompt0.v3_prompt0_builder import build_prompt0_v3


def _call_gpt_5(messages: List[Dict[str, str]]) -> str:
    import time
    model_name = os.getenv("AGENT7_LLM_MODEL", "gpt-5-nano")
    api_base = os.getenv("LLM_API_BASE") or os.getenv("OPENAI_API_BASE") or "https://api.nbai.art/v1"
    llm = create_llm(model_name=model_name, api_base=api_base, temperature=0.3, max_tokens=2000)
    t0 = time.time()
    print(f"[Agent7 v3] LangChain invoke model={model_name} base={api_base}")
    combined: List[str] = []
    for m in messages:
        role = m.get('role')
        content = m.get('content', '')
        combined.append(f"[{role}]\n{content}")
    text_input = "\n\n".join(combined)
    resp = llm.invoke(text_input)
    dt = time.time() - t0
    print(f"[Agent7 v3] LangChain response in {dt:.2f}s")
    return getattr(resp, 'content', str(resp)).strip()


def build_prompt1_v3(payload: Dict[str, Any], principles_zh: str) -> Dict[str, Any]:
    """先构造 prompt0（中文原则+输入），再用 gpt-5 产出 prompt1。"""
    p0 = build_prompt0_v3(payload, principles_zh)
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": "You are Agent7, an expert metaphorical visualization prompt writer."},
        {"role": "user", "content": p0["prompt0"]},
    ]
    print("[Agent7 v3] Generating prompt1 with LLM...")
    prompt1 = _call_gpt_5(messages)
    print("[Agent7 v3] prompt1 generated (length=", len(prompt1), ")")
    return {"prompt1": prompt1, "meta": {**p0["meta"], "llm": os.getenv("AGENT7_LLM_MODEL", "gpt-5-nano")}}


__all__ = ["build_prompt1_v3"]


