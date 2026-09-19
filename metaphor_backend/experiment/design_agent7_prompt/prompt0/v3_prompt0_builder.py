from typing import Dict, Any, List


def _map_datafact_to_verbs(data_fact: str) -> List[str]:
    if not data_fact:
        return ["rising"]
    text = data_fact.strip().lower()
    growth_keys = {"增长", "increase", "growth", "rising", "up", "expand", "expansion"}
    decline_keys = {"下降", "decrease", "decline", "fall", "drop", "down"}
    fluct_keys = {"波动", "fluctuation", "volatile", "oscillation", "swing"}
    peak_keys = {"峰值", "极值", "peak", "spike", "apex", "maximum"}
    steady_keys = {"平稳", "稳定", "steady", "flat", "constant"}
    if any(k in text for k in growth_keys):
        return ["rising", "thickening"]
    if any(k in text for k in decline_keys):
        return ["shrinking", "thinning"]
    if any(k in text for k in fluct_keys):
        return ["oscillating", "undulating"]
    if any(k in text for k in peak_keys):
        return ["spiking", "peaking"]
    if any(k in text for k in steady_keys):
        return ["steady", "flat"]
    return ["progressing", "clarifying"]


def build_prompt0_v3(payload: Dict[str, Any], principles_zh: str) -> Dict[str, Any]:
    """将中文指导原则与输入参数组装为英文 prompt0（供 Agent7 LLM 使用）。

    prompt0 作用：作为 LLM 的提示词（包含约束、输入摘要、映射与风格锚点），让 LLM 生成最终 prompt1。
    """
    keyword = payload.get("keyword", "metaphor")
    data_fact = payload.get("dataFact", "trend")
    context_desc = payload.get("contextDescription", "")
    default_plan: List[Dict[str, Any]] = payload.get("defaultPlan", [])

    verbs = _map_datafact_to_verbs(data_fact)
    verbs_str = ", ".join(verbs[:2])

    mappings_lines: List[str] = []
    for it in default_plan[:8]:
        field = it.get("dataField", "data")
        channels = ", ".join(it.get("channels", []) or ["position"])
        mappings_lines.append(f"- {field} -> {channels}")

    style_keywords = "clean vector graphics, abstract minimalism, data visualization clarity, cinematic clarity, sketch"

    prompt0_text = (
        "You are an expert metaphorical visualization designer.\n"
        "Your task is to produce ONE high-quality English prompt (prompt1) for a text-to-image model, following these Chinese design principles strictly.\n\n"
        "Chinese design principles (verbatim):\n"
        f"{principles_zh.strip()}\n\n"
        "Input summary:\n"
        f"- Metaphor subject: {keyword}\n"
        f"- Data fact (trend-level): {data_fact} (visual verbs: {verbs_str})\n"
        f"- Context: {context_desc or 'N/A'}\n"
        "- Given mappings (hard constraint; do NOT invent new channels; one dimension per channel; ≤4 channels total in use):\n"
        + "\n".join(mappings_lines) + "\n\n"
        "Output requirements (English only; no extra explanations outside the prompt):\n"
        "1) Start with: 'Generate a metaphorical conceptual sketch (vector, non-photorealistic).'\n"
        "2) Provide a concise set of constraints tailored to the above inputs and principles (not boilerplate).\n"
        "3) Provide a short heuristics list reflecting the subject and data fact (use the verbs).\n"
        "4) Provide a 'Content to render' section that rewrites mappings as natural-language annotations (dataField → channel), using the metaphor as the overall structure; keep channels within constraints.\n"
        "5) Provide 1–3 natural layout hints (no axes).\n"
        f"6) End with: 'Style keywords: {style_keywords}.'\n"
        "7) Append one trailing meta line starting with 'Meta:' explaining mapping pruning if any, otherwise 'Meta: no mapping reduction'.\n"
    ).strip()

    return {
        "prompt0": prompt0_text,
        "meta": {
            "keyword": keyword,
            "dataFact": data_fact,
            "contextDescription": context_desc,
            "verbs": verbs[:2],
            "style_keywords": style_keywords.split(", "),
        },
    }


__all__ = ["build_prompt0_v3"]


