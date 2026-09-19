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
        return "a clean horizontal line"
    if "band" in sid or "area" in sid or "region" in sid:
        return "layered bands"
    if "point" in sid or "dot" in sid:
        return "discrete dots"
    if "bar" in sid:
        return "uniform bars"
    if "arc" in sid or "ring" in sid:
        return "simple arcs"
    if "wave" in sid:
        return "wave-like shapes"
    return "simple geometric forms"


def _annotation_sentence(item: Dict[str, Any], keyword: str) -> str:
    data_field = item.get("dataField", "the data")
    subitem_id = item.get("subitemId", "")
    channels = item.get("channels", [])
    sub_desc = _describe_subitem(subitem_id)
    ch_phrase = _channels_to_phrase(channels)
    return (
        f"{data_field} → {', '.join(channels) or 'position'}: marked using {sub_desc} tied to the {keyword} metaphor, "
        f"encoded via {ch_phrase}."
    )


def build_prompt0(payload: Dict[str, Any]) -> Dict[str, Any]:
    """输入: {keyword, dataFact, contextDescription, defaultPlan}
    输出: {prompt0: 英文固定要求+内容, meta}
    """
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
        "Focus on data understanding first, metaphor second, decoration last.",
        "Simplify into clean vector-like graphics, abstract not photorealistic.",
        "Limit to 3–4 meaningful visual dimensions.",
        "Remove decorative backgrounds; keep negative space.",
        "Each data mapping corresponds to exactly one visual channel.",
        "Visual weight allocation: ~70% data, ~20% metaphor, ~10% decoration.",
        "Clear foreground–midground–background hierarchy.",
        "Minimal, harmonious color palette; minimal annotations, no text clutter.",
    ]

    heuristics = [
        f"Decide the central subject from {keyword}, then choose a presentation mode (prefer infographic).",
        f"Describe {data_fact} using dynamic visual changes: {verbs_str}.",
        "Convert each defaultPlan item into natural-language visual annotations clarifying the mapping.",
        "End with stable style anchors for consistency.",
    ]

    content_lines = [
        f"Central metaphor: {keyword}, representing {context_desc or 'the underlying data context' }.",
        f"Visual trend: express {data_fact} using {verbs_str}.",
        "Data mappings (rewrite into visual annotations):",
    ] + [f"- {a}" for a in annotations]

    style_keywords = (
        "infographic, metaphorical illustration, clean vector graphics, abstract minimalism, data visualization clarity, cinematic clarity"
    )

    prompt0_text = (
        "Generate a metaphorical infographic-style vector illustration.\n\n"
        "Constraints (must follow):\n- " + "\n- ".join(constraints) + "\n\n"
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
        },
    }


__all__ = ["build_prompt0"]


