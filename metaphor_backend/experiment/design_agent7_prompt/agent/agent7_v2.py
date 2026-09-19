from typing import Dict, Any

from experiment.design_agent7_prompt.prompt0.v2_prompt0_builder import build_prompt0_v2


def build_prompt1_v2(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Agent7 V2：基于 V2 指导原则的 Prompt0，作为 Prompt1 输出。"""
    p0 = build_prompt0_v2(payload)
    return {
        "prompt1": p0["prompt0"],
        "meta": p0["meta"],
    }


__all__ = ["build_prompt1_v2"]


