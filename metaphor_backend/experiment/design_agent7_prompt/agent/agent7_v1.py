from typing import Dict, Any

from experiment.design_agent7_prompt.prompt0.v1_prompt0_builder import build_prompt0


def build_prompt1(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Agent7 V1：将输入 + 固定英文要求(Prompt0) 组装，得到调用文生图 API 的 Prompt1。

    目前 Prompt1 等于 Prompt0 的正文；后续可在此处插入模型特定前后缀或参数化模版。
    返回 {prompt1, meta}。
    """
    p0 = build_prompt0(payload)
    prompt1 = p0["prompt0"]
    return {
        "prompt1": prompt1,
        "meta": p0["meta"],
    }


__all__ = ["build_prompt1"]


