import os
from typing import Dict, Any, List

import os
from utils.langchain_utils import create_llm
from experiment.design_agent7_prompt.prompt0.v4_prompt0_builder import build_prompt0_v4
from langchain.schema import HumanMessage, SystemMessage


def build_prompt1_v4(payload: Dict[str, Any], principles_zh: str) -> Dict[str, Any]:
    """V4：先构造 prompt0（中文原则+输入），再用 LangChain+gpt-4o-mini 产出 prompt1。"""
    p0 = build_prompt0_v4(payload, principles_zh)
    # model_name = os.getenv("AGENT7_LLM_MODEL", "o4-mini")
    model_name = os.getenv("AGENT7_LLM_MODEL", "gpt-5-nano")
    # api_base = "https://ai-yyds.com/v1"
    api_base = "https://api.nbai.art/v1"
    llm = create_llm(model_name=model_name, api_base=api_base, temperature=0.3, max_tokens=2000)

    # 与 guided_metaphor_agent 一致：用消息数组调用，并从 response.content 取文本
    messages = [
        SystemMessage(content="You are an expert metaphorical visualization prompt writer."),
        HumanMessage(content=p0["prompt0"]),
    ]

    print(f"[Agent7 v4] LangChain invoke model={model_name} base={api_base}")
    resp = llm.invoke(messages)
    content = resp.content.strip() if hasattr(resp, 'content') else str(resp).strip()
    if not content:
        # 打印更多调试信息
        try:
            meta = getattr(resp, 'response_metadata', {})
            extra = getattr(resp, 'additional_kwargs', {})
            print(f"[Agent7 v4] empty content. meta={meta} extra_keys={list(extra.keys())}")
        except Exception as e:
            print(f"[Agent7 v4] debug meta fail: {e}")

        # 回退策略1：仅传 HumanMessage
        try:
            print("[Agent7 v4] fallback: invoke with single HumanMessage")
            resp2 = llm.invoke([HumanMessage(content=p0["prompt0"])])
            content = resp2.content.strip() if hasattr(resp2, 'content') else str(resp2).strip()
        except Exception as e:
            print(f"[Agent7 v4] fallback1 error: {e}")

    if not content:
        # 回退策略2：当作纯文本调用
        try:
            print("[Agent7 v4] fallback: invoke with raw text input")
            resp3 = llm.invoke(p0["prompt0"])  # type: ignore[arg-type]
            content = resp3.content.strip() if hasattr(resp3, 'content') else str(resp3).strip()
        except Exception as e:
            print(f"[Agent7 v4] fallback2 error: {e}")
    print(f"[Agent7 v4] prompt1 generated (length={len(content)})")

    return {"prompt1": content, "meta": {**p0["meta"], "llm": model_name, "version": "v4"}}


__all__ = ["build_prompt1_v4"]


