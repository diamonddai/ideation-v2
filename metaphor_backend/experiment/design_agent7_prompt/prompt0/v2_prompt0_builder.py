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


def _channels_to_phrase(channels: List[str]) -> str:
    mapping = {
        "position": "the position channel",
        "size": "the size channel",
        "lightness": "the lightness channel",
        "color": "the color channel",
        "texture": "the texture channel",
        "orientation": "the orientation channel",
        "shape": "the shape channel",
    }
    if not channels:
        return "the position channel"
    phrases = [mapping.get(ch, ch) for ch in channels]
    return "and".join([" "+p for p in phrases]).strip()


def _describe_subitem(subitem_id: str) -> str:
    sid = (subitem_id or "").lower()
    if "line" in sid:
        return "a minimal line"
    if "band" in sid or "area" in sid or "region" in sid:
        return "abstract bands"
    if "point" in sid or "dot" in sid:
        return "sparse dots"
    if "bar" in sid:
        return "uniform bars"
    if "arc" in sid or "ring" in sid:
        return "concentric rings"
    if "wave" in sid:
        return "flowing wave shapes"
    return "simple geometric primitives"


def _annotation_sentence(item: Dict[str, Any], keyword: str) -> str:
    data_field = item.get("dataField", "the data")
    subitem_id = item.get("subitemId", "")
    channels = item.get("channels", [])
    sub_desc = _describe_subitem(subitem_id)
    ch_phrase = _channels_to_phrase(channels)
    return (
        f"{data_field} → {', '.join(channels) or 'position'}: sketched with {sub_desc}, encoded via {ch_phrase}, "
        f"using {keyword} as the overall structure."
    )


def build_prompt0_v2(payload: Dict[str, Any]) -> Dict[str, Any]:
    """基于 V2 指导原则构造 Prompt0。定位为概念性视觉线稿，隐喻即结构、数据表达趋势即可。"""
    keyword = payload.get("keyword", "metaphor")
    data_fact = payload.get("dataFact", "trend")
    context_desc = payload.get("contextDescription", "")
    default_plan = payload.get("defaultPlan", [])

    verbs = _map_datafact_to_verbs(data_fact)
    verbs_str = ", ".join(verbs[:2])

    annotations: List[str] = []
    for item in default_plan[:4]:
        annotations.append(_annotation_sentence(item, keyword))

    constraints = [
        "Produce a conceptual sketch (~30% completeness) with {keyword} as the overall structure.",
        "Do not render precise values; focus on relative relationships and trends.",
        "Use abstract vector primitives; non-photorealistic; crisp minimal composition.",
        "Limit to 3–4 visual channels strictly derived from input; do not invent channels.",
        "One data dimension maps to exactly one visual channel (no reuse).",
        "Remove decorative textures/background; preserve generous negative space.",
        "Clear foreground–midground–background hierarchy; avoid heavy overlap.",
        "Low-saturation harmonious palette; reduce hues unless color is a mapping channel.",
        "Minimize text; avoid dense labels and large paragraphs.",
        "Ban axes; prefer natural layouts driven by the metaphorical structure.",
        "No infographic-style verbose callouts near the subject; keep the scene clean.",
        "No photorealism; no photography texture; no unrelated ornament.",
    ]

    heuristics = [
        f"Treat {keyword} as the overall structure to encode data (not 'like a chart').",
        f"Describe {data_fact} using controlled dynamic descriptors: {verbs_str}.",
        "Rewrite each defaultPlan mapping into natural-language visual annotations (data → channel).",
        "Prefer positional encoding for time/order to improve reading flow.",
        "End with stable style anchors for consistent outputs.",
    ]

    natural_layout_examples = [
        "arranged as concentric rings like tree rings",
        "displayed as a flowing hourglass shape",
        "scattered across a field of poppies",
    ]

    content_lines = [
        f"Overall metaphorical structure: {keyword}, conveying {context_desc or 'the underlying context'}.",
        f"Visual trend emphasis: express {data_fact} using {verbs_str}; trend-level fidelity only.",
        "Data mappings (rewrite as visual annotations):",
    ] + [f"- {a}" for a in annotations] + [
        "Natural layout hints (no axes):",
    ] + [f"- {e}" for e in natural_layout_examples]

    style_keywords = (
        "clean vector graphics, abstract minimalism, data visualization clarity, cinematic clarity, sketch"
    )

    prompt0_text = (
        "Generate a metaphorical conceptual sketch (vector, non-photorealistic).\n\n"
        "Constraints (must follow):\n- " + "\n- ".join(constraints).replace("{keyword}", keyword) + "\n\n"
        "Heuristics (apply explicitly):\n- " + "\n- ".join(heuristics) + "\n\n"
        "Content to render:\n" + "\n".join(content_lines) + "\n\n"
        f"Style keywords: {style_keywords}."
    ).strip()

    return {
        "prompt0": prompt0_text,
        "meta": {
            "keyword": keyword,
            "dataFact": data_fact,
            "contextDescription": context_desc,
            "verbs": verbs[:2],
            "annotations": annotations,
            "style_keywords": style_keywords.split(", "),
            "natural_layout_examples": natural_layout_examples,
        },
    }


__all__ = ["build_prompt0_v2"]


