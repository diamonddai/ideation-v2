"""
Agent6: 映射构建 Agent
使用共享的映射决策逻辑
"""

from typing import Dict, Any, List
from uuid import uuid4
import os
import json
import re
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# 尝试导入共享逻辑，如果失败则提供后备方案
try:
    from .unified_mapping_logic import get_shared_mapping_decision
    USE_SHARED_LOGIC = True
except ImportError:
    print("⚠️ 无法导入unified_mapping_logic，使用简化逻辑")
    USE_SHARED_LOGIC = False


def clean_json_response(text: str) -> dict:
    """清理LLM响应并解析JSON"""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    
    if '```json' in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    elif '```' in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]
    
    return json.loads(text)


def llm_generate(prompt: str) -> str:
    """调用LLM生成内容"""
    chat = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
    )
    return chat([
        SystemMessage(content="You are an expert in visualization metaphors. Return valid JSON only."),
        HumanMessage(content=prompt)
    ]).content.strip()


class MappingAgent:
    """Agent6：映射构建代理"""
    
    def __init__(self):
        self.name = "MappingAgent"
    
    def run(self,
            field: str,
            field1: str,
            field2: str,
            keyword: str,
            data_fact: str,
            context_description: str) -> Dict[str, Any]:
        """
        主运行函数
        
        流程：
        1. 生成subitems（隐喻的视觉部件）
        2. 使用共享逻辑决定最佳映射（如果可用）
        3. 构建完整的mapping_spec
        """
        
        mapping_id = f"map_{uuid4().hex[:8]}"
        
        # 第一阶段：生成subitems
        print(f"🎯 Agent6: 为'{keyword}'生成视觉部件...")
        subitems = self._generate_subitems(keyword, data_fact, context_description)
        
        # 第二阶段：决定最佳映射
        if USE_SHARED_LOGIC:
            print(f"🎯 Agent6: 使用共享逻辑决定映射...")
            mapping_decision = get_shared_mapping_decision(
                keyword=keyword,
                field1=field1,
                field2=field2,
                data_fact=data_fact,
                context_description=context_description,
                subitems=subitems
            )
        else:
            print(f"🎯 Agent6: 使用简化逻辑...")
            mapping_decision = self._simple_mapping_decision(field1, field2, subitems)
        
        # 第三阶段：构建mapping_spec
        mapping_spec = self._build_mapping_spec(
            mapping_id=mapping_id,
            keyword=keyword,
            data_fact=data_fact,
            context_description=context_description,
            field1=field1,
            field2=field2,
            subitems=subitems,
            mapping_decision=mapping_decision
        )
        
        return mapping_spec
    
    def _generate_subitems(self, keyword: str, data_fact: str, context_description: str) -> List[Dict]:
        """生成隐喻的视觉部件"""
        
        prompt = f"""
Based on "{keyword}", generate 3-5 visual components of the metaphor vehicle.

Requirements:
- Specific parts of {keyword} (not generic)
- Each: name, geometry (point/line/area), brief description
- Include variety in geometry

Examples:
- flower: petal (area), stalk (line), pistil (point)
- tree: leaf (point), branch (line), canopy (area)

Context:
- Metaphor: {keyword}
- Data: {data_fact}

JSON only:
{{
  "subitems": [
    {{"name": "<name>", "geometry": "point|line|area", "description": "<desc>"}},
    ...
  ]
}}
"""
        
        try:
            raw = llm_generate(prompt)
            result = clean_json_response(raw)
            subitems = result.get("subitems", [])
            
            # 添加ID
            for i, item in enumerate(subitems):
                item["subitem_id"] = f"sub_{i+1:02d}"
            
            print(f"✅ 生成了 {len(subitems)} 个subitems")
            return subitems
            
        except Exception as e:
            print(f"⚠️ Subitem生成失败: {e}，使用默认值")
            return [
                {"subitem_id": "sub_01", "name": "main element", "geometry": "area", "description": "Primary visual"},
                {"subitem_id": "sub_02", "name": "detail", "geometry": "point", "description": "Detail markers"},
                {"subitem_id": "sub_03", "name": "connector", "geometry": "line", "description": "Connecting lines"}
            ]
    
    def _simple_mapping_decision(self, field1: str, field2: str, subitems: List[Dict]) -> Dict:
        """简化的映射决策（后备方案）"""
        return {
            "field1_mapping": {
                "subitem_name": subitems[0]["name"] if subitems else "element",
                "geometry": subitems[0]["geometry"] if subitems else "area",
                "channels": ["color"],
                "rationale": "Default"
            },
            "field2_mapping": {
                "subitem_name": subitems[1]["name"] if len(subitems) > 1 else subitems[0]["name"],
                "geometry": subitems[1]["geometry"] if len(subitems) > 1 else "area",
                "channels": ["size"],
                "rationale": "Default"
            },
            "overall_reasoning": "Using simplified logic"
        }
    
    def _build_mapping_spec(self,
                           mapping_id: str,
                           keyword: str,
                           data_fact: str,
                           context_description: str,
                           field1: str,
                           field2: str,
                           subitems: List[Dict],
                           mapping_decision: Dict) -> Dict[str, Any]:
        """构建完整的mapping_spec"""
        
        # 提取映射决策
        f1_mapping = mapping_decision["field1_mapping"]
        f1_subitem_name = f1_mapping["subitem_name"]
        f1_channels = f1_mapping["channels"]
        
        f2_mapping = mapping_decision["field2_mapping"]
        f2_subitem_name = f2_mapping["subitem_name"]
        f2_channels = f2_mapping["channels"]
        
        # 找到对应的subitem_id
        f1_subitem_id = None
        f2_subitem_id = None
        
        for s in subitems:
            if s["name"] == f1_subitem_name:
                f1_subitem_id = s["subitem_id"]
            if s["name"] == f2_subitem_name:
                f2_subitem_id = s["subitem_id"]
        
        # 如果找不到，使用第一个和第二个
        if not f1_subitem_id:
            f1_subitem_id = subitems[0]["subitem_id"] if subitems else "sub_01"
            f1_subitem_name = subitems[0]["name"] if subitems else "element"
        
        if not f2_subitem_id:
            f2_subitem_id = subitems[1]["subitem_id"] if len(subitems) > 1 else f1_subitem_id
            f2_subitem_name = subitems[1]["name"] if len(subitems) > 1 else f1_subitem_name
        
        # 构建defaultPlan
        default_plan = [
            {
                "dataField": field1,
                "subitemId": f1_subitem_id,
                "subitemName": f1_subitem_name,
                "channels": f1_channels
            },
            {
                "dataField": field2,
                "subitemId": f2_subitem_id,
                "subitemName": f2_subitem_name,
                "channels": f2_channels
            }
        ]
        
        # 构建完整spec
        mapping_spec = {
            "mapping_id": mapping_id,
            "keyword": keyword,
            "dataFact": data_fact,
            "contextDescription": context_description,
            "defaultPlan": default_plan,
            "field1": {
                "dataField": field1,
                "subitemOptions": subitems,
                "channels": {
                    "allowed": ["position", "size", "lightness", "color", "texture", "orientation", "shape"],
                    "default": f1_channels
                }
            },
            "field2": {
                "dataField": field2,
                "subitemOptions": subitems,
                "channels": {
                    "allowed": ["position", "orientation", "lightness", "color", "texture", "size", "shape"],
                    "default": f2_channels
                }
            },
            "mapping_reasoning": mapping_decision.get("overall_reasoning", "")
        }
        
        print("=" * 80)
        print("✅ Agent6 生成的 defaultPlan:")
        for i, row in enumerate(default_plan):
            print(f"  Row {i+1}: {row['dataField']} → {row['subitemName']} via {row['channels']}")
        print("=" * 80)
        
        return mapping_spec

# """
# Agent6: 映射构建 Agent（MappingAgent）
# 作用：根据数据字段、本体-喻体关键词、数据特征和上下文信息，构建视觉隐喻映射通道
# """
# # agent6.py
# from typing import Dict, Any, List
# from uuid import uuid4
# import os, json,re
# from langchain_openai import ChatOpenAI
# from langchain.schema import HumanMessage, SystemMessage

# def clean_json_response(text: str) -> dict:
#     """清理LLM响应并解析JSON"""
#     # 移除<think></think>标签
#     text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
#     text = re.sub(r'<[^>]+>', '', text)
#     text = text.strip()
    
#     # 处理markdown代码块
#     if '```json' in text:
#         match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
#         if match:
#             text = match.group(1)
#     elif '```' in text:
#         match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
#         if match:
#             text = match.group(1)
    
#     # 找到JSON边界
#     start_idx = text.find('{')
#     end_idx = text.rfind('}')
    
#     if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
#         text = text[start_idx:end_idx + 1]
    
#     return json.loads(text)

# def llm_generate(prompt: str) -> str:
#     chat = ChatOpenAI(
#             model="gpt-4o-mini",
#             temperature=0.4,
#             openai_api_key=os.getenv("OPENAI_API_KEY"),
#             openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
#         )
#     return chat([SystemMessage(content="You are an expert in visualization metaphors. "
#     "Return a single valid JSON object only, in English (US). "
#     "Follow the schema and enumerations strictly."),
#                  HumanMessage(content=prompt)]).content.strip()

# class MappingAgent:
#     """Agent6：根据 keyword 动态生成点/线/面子项与映射方案，返回你确定的 Agent6 输出结构。"""
#     def __init__(self):
#         self.name = "MappingAgent"
    
#     def run(self,
#             field: str,
#             field1: str,
#             field2: str,
#             keyword: str,
#             data_fact: str,
#             context_description: str) -> Dict[str, Any]:

#         mapping_id = f"map_{uuid4().hex[:8]}"




    
# #版本2:
#         prompt = f"""
#         Return a SINGLE JSON object (no explanation, no Markdown). ALL STRINGS MUST BE ENGLISH (US).

#         [Task]
#         - Based on the metaphor keyword "{keyword}", construct 3–5 visual subitems that are concrete components of the metaphor (not generic names).
#           * Each subitem has: subitem_id, name, geometry ∈ {{point, line, area}}.
#           * Names MUST tie to the metaphor. Avoid generic terms.
#             * Good examples:
#             - Hourglass → "sand grains" (point), "falling sand stream" (line), "lower bulb sand mound" (area)
#             - Tree → "leaf markers" (point), "trunk growth line" (line), "canopy area" (area)
#             - River → "pebble markers" (point), "river flow line" (line), "riverbed area" (area)
            
#         - Build two field blocks (field1 and field2). They MUST reuse the SAME subitems (membership identical), but **ordering may differ**.

#         - Channels configuration rules:
#           * Both field1 and field2:
#               allowed = ["position","size","lightness","color","texture","orientation","shape"] (field1 order)
#               allowed = ["position","orientation","lightness","color","texture","size","shape"] (field2 order)
              
#           * ✅ INTELLIGENT DEFAULT SELECTION (NEW):
#             Choose field1.channels.default and field2.channels.default based on data semantics:
            
#             - If field name suggests CATEGORICAL data (contains: "type", "category", "genre", "class", "group", "kind"):
#               → default should be ["color"] (categories are best encoded by color)
              
#             - If field name suggests QUANTITATIVE data (contains: "revenue", "sales", "worldwide", "count", "number", "amount", "value", "score", "rating"):
#               → default should be ["size"] (quantities are best encoded by size)
              
#             - If field name suggests TEMPORAL data (contains: "time", "date", "year", "month", "day", "period"):
#               → default should be ["position"] (time is best encoded by position along axis)
              
#             - If field name suggests ORDINAL data (contains: "rank", "level", "grade", "priority"):
#               → default could be ["lightness"] or ["position"]
              
#             - If uncertain, use:
#               field1.default = ["color"]  (first dimension often categorical)
#               field2.default = ["size"]   (second dimension often quantitative)

#         - Compose defaultPlan with EXACTLY TWO rows and STRICTLY as follows:
#           * Row 1 (for field1):
#               dataField   = "{field1}"
#               subitemId   = the subitem_id of the FIRST item in field1.subitemOptions
#               subitemName = the name of that FIRST item
#               channels    = field1.channels.default  ← 使用智能选择的default
#           * Row 2 (for field2):
#               dataField   = "{field2}"
#               subitemId   = the subitem_id of the FIRST item in field2.subitemOptions
#               subitemName = the name of that FIRST item
#               channels    = field2.channels.default  ← 使用智能选择的default
              
#         - The first subitem in field1.subitemOptions MUST NOT be the same subitem_id as the first in field2.subitemOptions.
#           If they would otherwise be the same, reorder field2.subitemOptions so its first item is different (membership stays identical).

#         [Inputs]
#         - field(compat): {field}
#         - field1: {field1}  ← 例如 "type" (会被识别为categorical)
#         - field2: {field2}  ← 例如 "worldwide" (会被识别为quantitative)
#         - keyword: {keyword}
#         - dataFact: {data_fact}
#         - contextDescription: {context_description}

#         [OUTPUT JSON (keys and hierarchy MUST match exactly)]
#         {{
#           "mapping_id": "{mapping_id}",
#           "keyword": "{keyword}",
#           "dataFact": "{data_fact}",
#           "contextDescription": "{context_description}",
#           "defaultPlan": [
#             {{ "dataField": "{field1}", "subitemId": "<= field1.subitemOptions[0].subitem_id>", "subitemName": "<= that item's name>", "channels": ["<= intelligently chosen for {field1}>"] }},
#             {{ "dataField": "{field2}", "subitemId": "<= field2.subitemOptions[0].subitem_id>", "subitemName": "<= that item's name>", "channels": ["<= intelligently chosen for {field2}>"] }}
#           ],
#           "field1": {{
#             "dataField": "{field1}",
#             "subitemOptions": [
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
#             ],
#             "channels": {{
#               "allowed":  ["position","size","lightness","color","texture","orientation","shape"],
#               "default":  ["<intelligently chosen based on {field1} semantics>"]
#             }}
#           }},
#           "field2": {{
#             "dataField": "{field2}",
#             "subitemOptions": [
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#               {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
#             ],
#             "channels": {{
#               "allowed":  ["position","orientation","lightness","color","texture","size","shape"],
#               "default":  ["<intelligently chosen based on {field2} semantics>"]
#             }}
#           }}
#         }}

#         [STRICT REQUIREMENTS]
#         - Output ONE valid JSON object; no extra text/Markdown.
#         - 3-5 metaphor-specific subitems
#         - defaultPlan MUST contain exactly two rows, one for "{field1}" and one for "{field2}".
#         - defaultPlan rows MUST mirror the FIRST item of each field's subitemOptions and MUST copy the field's channels.default.
#         - defaultPlan.subitemId MUST exist in the corresponding field block's subitemOptions; defaultPlan.subitemName MUST equal that subitem's name.
#         - All strings MUST be English; geometry ∈ {{point, line, area}}.
#         - ✅ DEFAULT CHANNELS MUST BE INTELLIGENTLY CHOSEN based on field semantics, not hardcoded!
#         """.strip()
#         # 只保留必要约束：三类几何、七个通道、默认方案的判定规则
#         prompt = f"""
# Return a SINGLE JSON object (no explanation, no Markdown). ALL STRINGS MUST BE ENGLISH (US).

# [Task]
# - Based on the metaphor keyword "{keyword}", construct 3–5 visual subitems that are concrete components of the metaphor (not generic names).
#   * Each subitem has: subitem_id, name, geometry ∈ {{point, line, area}}.
#   * Names MUST tie to the metaphor.
#     * Good examples:
#     - Hourglass → "sand grains" (point), "sand stream" (line), "sand mound" (area)
#     - Tree → "tree leaf" (point), "tree branch" (line), "tree canopy" (area)
#     - River →  "river flow line" (line), "riverbed area" (area)
# - Build two field blocks (field1 and field2).They MUST reuse the SAME subitems (membership identical), but **ordering may differ**.
# - Channels configuration rules:
#   * Both field1 and field2:
#       allowed = ["position","size","lightness","color","texture","orientation","shape"] (field1 order)
#       allowed = ["position","orientation","lightness","color","texture","size","shape"] (field2 order)
# * ✅ INTELLIGENT DEFAULT SELECTION (NEW):
#     Choose field1.channels.default and field2.channels.default based on data semantics:
    
#     - If field name suggests CATEGORICAL data (contains: "type", "category", "genre", "class", "group", "kind"):
#       → default should be ["color"] (categories are best encoded by color)
      
#     - If field name suggests QUANTITATIVE data (contains: "revenue", "sales", "worldwide", "count", "number", "amount", "value", "score", "rating"):
#       → default should be ["size"] (quantities are best encoded by size)
      
#     - If field name suggests TEMPORAL data (contains: "time", "date", "year", "month", "day", "period"):
#       → default should be ["position"] (time is best encoded by position along axis)
      
#     - If field name suggests ORDINAL data (contains: "rank", "level", "grade", "priority"):
#       → default could be ["lightness"] or ["position"]
      
#     - If uncertain, use:
#       field1.default = ["color"]  (first dimension often categorical)
#       field2.default = ["size"]   (second dimension often quantitative)

# - Compose defaultPlan with EXACTLY TWO rows and STRICTLY as follows:
#   * Row 1 (for field1):
#       dataField   = "{field1}"
#       subitemId   = the subitem_id of the FIRST item in field1.subitemOptions
#       subitemName = the name of that FIRST item
#       channels    = field1.channels.default  ← 使用智能选择的default
#   * Row 2 (for field2):
#       dataField   = "{field2}"
#       subitemId   = the subitem_id of the FIRST item in field2.subitemOptions
#       subitemName = the name of that FIRST item
#       channels    = field2.channels.default  ← 使用智能选择的default
# - The first subitem in field1.subitemOptions MUST NOT be the same subitem_id as the first in field2.subitemOptions.
#   If they would otherwise be the same, reorder field2.subitemOptions so its first item is different (membership stays identical).

# [Inputs]
# - field(compat): {field}
# - field1: {field1}
# - field2: {field2}
# - keyword: {keyword}
# - dataFact: {data_fact}
# - contextDescription: {context_description}

# [OUTPUT JSON (keys and hierarchy MUST match exactly)]
# {{
#   "mapping_id": "{mapping_id}",
#   "keyword": "{keyword}",
#   "dataFact": "{data_fact}",
#   "contextDescription": "{context_description}",
#   "defaultPlan": [
#     {{ "dataField": "{field1}", "subitemId": "<= field1.subitemOptions[0].subitem_id>", "subitemName": "<= that item's name>", "channels": ["<= field1.channels.default ...>"] }},
#     {{ "dataField": "{field2}", "subitemId": "<= field2.subitemOptions[0].subitem_id>", "subitemName": "<= that item's name>", "channels": ["<= field2.channels.default ...>"] }}
#   ],
#   "field1": {{
#     "dataField": "{field1}",
#     "subitemOptions": [
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
#     ],
#     "channels": {{
#       "allowed":  ["position","size","lightness","color","texture","orientation","shape"],
#       "default":  ["size"]
#     }}
#   }},
#   "field2": {{
#     "dataField": "{field2}",
#     "subitemOptions": [
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
#       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
#     ],
#     "channels": {{
#       "allowed":  ["position","orientation","lightness","color","texture","size","shape"],
#       "default":  ["position"]
#     }}
#   }}
# }}

# [STRICT REQUIREMENTS]
# - Output ONE valid JSON object; no extra text/Markdown.
# - 3-5 metaphor-specific subitems
# - defaultPlan MUST contain exactly two rows, one for "{field1}" and one for "{field2}".
# - defaultPlan rows MUST mirror the FIRST item of each field's subitemOptions and MUST copy the field's channels.default.
# - defaultPlan.subitemId MUST exist in the corresponding field block's subitemOptions; defaultPlan.subitemName MUST equal that subitem's name.
# - All strings MUST be English; geometry ∈ {{point, line, area}}.
# """.strip()

#         raw = llm_generate(prompt)
#         try:
#             obj = clean_json_response(raw)
#             return obj
#         except Exception as e:
#             # 直接抛出错误，不生成占位数据
#             error_msg = f"MappingAgent failed to parse LLM response: {str(e)}"
#             print(error_msg)
#             print(f"Raw response (first 500 chars): {raw[:500]}")
#             raise ValueError(error_msg)
#         # try:
#         #     obj = clean_json_response(raw)
            
#         #     print("=" * 80)
#         #     print("✅ Agent6 生成的原始mapping_spec:")
#         #     print(json.dumps(obj, indent=2, ensure_ascii=False))
#         #     print("=" * 80)
            
#         #     # 验证并修复映射关系
#         #     obj = self._validate_and_fix_mapping(obj, field1, field2)
            
#         #     print("=" * 80)
#         #     print("✅ Agent6 验证后的最终mapping_spec:")
#         #     print(json.dumps(obj, indent=2, ensure_ascii=False))
#         #     print("=" * 80)
            
#         #     return obj
#         # except Exception as e:
#         #     error_msg = f"MappingAgent failed to parse LLM response: {str(e)}"
#         #     print(error_msg)
#         #     print(f"Raw response (first 500 chars): {raw[:500]}")
#         #     raise ValueError(error_msg)


# # ##版本3:
# #         prompt = f"""
# # Return a SINGLE JSON object (no explanation, no Markdown). ALL STRINGS MUST BE ENGLISH (US).

# # [Task]
# # - Based on the metaphor keyword "{keyword}", construct 3–5 visual subitems that are concrete components of the metaphor (not generic names).
# #   * Each subitem has: subitem_id, name, geometry ∈ {{point, line, area}}.
# #   * Names MUST tie to the metaphor.
# #     * Good examples:
# #     - Hourglass → "sand grains" (point), "sand stream" (line), "sand mound" (area)
# #     - Tree → "tree leaf" (point), "tree branch" (line), "tree canopy" (area)
# #     - River →  "river flow line" (line), "riverbed area" (area)
# #     - Flower → "flower petal" (area), "flower stalk" (line), "flower center" (point)
    
# # - Build two field blocks (field1 and field2). They MUST reuse the SAME subitems (membership identical), but **ordering may differ**.

# # - Channels configuration rules:
# #   * Both field1 and field2:
# #       allowed = ["position","size","lightness","color","texture","orientation","shape"] (field1 order)
# #       allowed = ["position","orientation","lightness","color","texture","size","shape"] (field2 order)
      
# #   * ✅ INTELLIGENT DEFAULT SELECTION:
# #     Choose field1.channels.default and field2.channels.default based on data semantics:
    
# #     - If field name suggests CATEGORICAL data (contains: "type", "category", "genre", "class", "group", "kind", "country", "region"):
# #       → default should be ["color"] (categories are best encoded by color)
      
# #     - If field name suggests QUANTITATIVE data (contains: "revenue", "sales", "worldwide", "count", "number", "amount", "value", "score", "rating", "rank", "happiness"):
# #       → default should be ["size"] (quantities are best encoded by size)
      
# #     - If field name suggests TEMPORAL data (contains: "time", "date", "year", "month", "day", "period"):
# #       → default should be ["position"] (time is best encoded by position along axis)
      
# #     - If field name suggests ORDINAL data (contains: "level", "grade", "priority"):
# #       → default could be ["lightness"] or ["position"]
      
# #     - If uncertain, use:
# #       field1.default = ["color"]  (first dimension often categorical)
# #       field2.default = ["size"]   (second dimension often quantitative)

# # - ⚠️ CRITICAL: Compose defaultPlan with EXACTLY TWO rows and STRICTLY in THIS ORDER:
# #   * Row 1 (MUST be for field1="{field1}"):
# #       dataField   = "{field1}"
# #       subitemId   = the subitem_id of the FIRST item in field1.subitemOptions
# #       subitemName = the name of that FIRST item
# #       channels    = field1.channels.default
      
# #   * Row 2 (MUST be for field2="{field2}"):
# #       dataField   = "{field2}"
# #       subitemId   = the subitem_id of the FIRST item in field2.subitemOptions
# #       subitemName = the name of that FIRST item
# #       channels    = field2.channels.default
      
# # - The first subitem in field1.subitemOptions MUST NOT be the same subitem_id as the first in field2.subitemOptions.
# #   If they would otherwise be the same, reorder field2.subitemOptions so its first item is different (membership stays identical).

# # [Inputs]
# # - field(compat): {field}
# # - field1: {field1}  ← 例如 "country" (categorical → color)
# # - field2: {field2}  ← 例如 "happiness rank" (quantitative → size)
# # - keyword: {keyword}
# # - dataFact: {data_fact}
# # - contextDescription: {context_description}

# # [OUTPUT JSON (keys and hierarchy MUST match exactly)]
# # {{
# #   "mapping_id": "{mapping_id}",
# #   "keyword": "{keyword}",
# #   "dataFact": "{data_fact}",
# #   "contextDescription": "{context_description}",
# #   "defaultPlan": [
# #     {{ "dataField": "{field1}", "subitemId": "<field1.subitemOptions[0].subitem_id>", "subitemName": "<field1.subitemOptions[0].name>", "channels": ["<intelligently chosen for {field1}>"] }},
# #     {{ "dataField": "{field2}", "subitemId": "<field2.subitemOptions[0].subitem_id>", "subitemName": "<field2.subitemOptions[0].name>", "channels": ["<intelligently chosen for {field2}>"] }}
# #   ],
# #   "field1": {{
# #     "dataField": "{field1}",
# #     "subitemOptions": [
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
# #     ],
# #     "channels": {{
# #       "allowed":  ["position","size","lightness","color","texture","orientation","shape"],
# #       "default":  ["<intelligently chosen based on {field1} semantics>"]
# #     }}
# #   }},
# #   "field2": {{
# #     "dataField": "{field2}",
# #     "subitemOptions": [
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
# #     ],
# #     "channels": {{
# #       "allowed":  ["position","orientation","lightness","color","texture","size","shape"],
# #       "default":  ["<intelligently chosen based on {field2} semantics>"]
# #     }}
# #   }}
# # }}

# # [STRICT REQUIREMENTS]
# # - Output ONE valid JSON object; no extra text/Markdown.
# # - 3-5 metaphor-specific subitems
# # - defaultPlan MUST contain exactly two rows: first for "{field1}", second for "{field2}"
# # - defaultPlan rows MUST mirror the FIRST item of each field's subitemOptions
# # - defaultPlan.subitemId MUST exist in the corresponding field block's subitemOptions
# # - All strings MUST be English; geometry ∈ {{point, line, area}}
# # - DEFAULT CHANNELS MUST BE INTELLIGENTLY CHOSEN based on field semantics!
# # """.strip()

# #         print("=" * 80)
# #         print("📝 Agent6 发送给LLM的Prompt:")
# #         print(prompt)
# #         print("=" * 80)

# #         raw = llm_generate(prompt)
        
# #         try:
# #             obj = clean_json_response(raw)
            
# #             print("=" * 80)
# #             print("✅ Agent6 生成的原始mapping_spec:")
# #             print(json.dumps(obj, indent=2, ensure_ascii=False))
# #             print("=" * 80)
            
# #             # 验证并修复映射关系
# #             obj = self._validate_and_fix_mapping(obj, field1, field2)
            
# #             print("=" * 80)
# #             print("✅ Agent6 验证后的最终mapping_spec:")
# #             print(json.dumps(obj, indent=2, ensure_ascii=False))
# #             print("=" * 80)
            
# #             return obj
# #         except Exception as e:
# #             error_msg = f"MappingAgent failed to parse LLM response: {str(e)}"
# #             print(error_msg)
# #             print(f"Raw response (first 500 chars): {raw[:500]}")
# #             raise ValueError(error_msg)


# #         prompt = f"""
# # Return a SINGLE JSON object (no explanation, no Markdown). ALL STRINGS MUST BE ENGLISH (US).

# # [Task]
# # - Based on the metaphor keyword "{keyword}", construct 3–5 visual subitems that are concrete components of the metaphor (not generic names).
# #   * Each subitem has: subitem_id, name, geometry ∈ {{point, line, area}}.
# #   * Names MUST tie to the metaphor. Avoid generic terms.
# #     * Good examples:
# #     - Hourglass → "sand grains" (point), "falling sand stream" (line), "lower bulb sand mound" (area)
# #     - Tree → "leaf markers" (point), "trunk growth line" (line), "canopy area" (area)
# #     - River → "pebble markers" (point), "river flow line" (line), "riverbed area" (area)
# #     - Palette → "color blocks" (area), "brush stroke" (line), "paint dots" (point)
    
# # - Build two field blocks (field1 and field2). They MUST reuse the SAME subitems (membership identical), but **ordering may differ**.

# # [VISUAL ENCODING GUIDELINES]
# # Choose appropriate channels based on data type semantics. Here are the complete mappings:

# # 1. **position** (位置) - MOST VERSATILE
# #    - ✅ Categorical data (nominal): Different positions for different categories
# #    - ✅ Ordinal data: Sequential positions along axis
# #    - ✅ Quantitative data: Continuous position mapping
# #    - Best for: Time series, rankings, any ordered data

# # 2. **color** (颜色/色相) 
# #    - ✅ Categorical data (nominal): Different hues for different categories
# #    - ⚠️ Can encode ordinal but lightness is better
# #    - Best for: Types, genres, categories, classes

# # 3. **lightness** (亮度/明度)
# #    - ✅ Ordinal data: Light → Dark gradient
# #    - ✅ Quantitative data: Continuous lightness mapping
# #    - ❌ NOT for categorical (hard to distinguish many shades)
# #    - Best for: Intensity, density, concentration, amounts

# # 4. **size** (尺寸/大小)
# #    - ✅ Ordinal data: Small → Large sequence
# #    - ✅ Quantitative data: Proportional sizing
# #    - ❌ NOT ideal for categorical (no natural ordering)
# #    - Best for: Revenue, count, population, magnitude

# # 5. **orientation** (方向/斜度/角度)
# #    - ✅ Categorical data: Different angles for categories
# #    - ✅ Ordinal data: Progressive angle changes
# #    - ⚠️ Can encode quantitative but less intuitive
# #    - Best for: Directions, trends, slopes, rotations

# # 6. **shape** (形状)
# #    - ✅ Categorical data (nominal): Different shapes for categories
# #    - ❌ NOT for ordinal or quantitative (no natural ordering)
# #    - Best for: Types, classes, symbols (e.g., ●▲■◆)

# # 7. **texture** (纹理)
# #    - ✅ Categorical data (nominal): Different patterns for categories
# #    - ❌ NOT for ordinal or quantitative
# #    - Best for: Material types, surface qualities, patterns

# # [INTELLIGENT CHANNEL SELECTION RULES]
# # Analyze field1 ("{field1}") and field2 ("{field2}") to determine their data types:

# # **Data Type Detection (by field name keywords):**

# # A. CATEGORICAL/NOMINAL (分类数据):
# #    - Keywords: "type", "category", "genre", "class", "kind", "group", "name", "label"
# #    - Best channels (in priority order):
# #      1. color (most effective)
# #      2. shape (if ≤7 categories)
# #      3. texture (if shape not suitable)
# #      4. position (as fallback)
# #    - Example: "movie type" → default: ["color"]

# # B. QUANTITATIVE (定量数据):
# #    - Keywords: "revenue", "sales", "worldwide", "amount", "value", "count", "number", "total", "score", "rating", "price", "cost"
# #    - Best channels (in priority order):
# #      1. size (most intuitive)
# #      2. position (second best)
# #      3. lightness (for intensity)
# #    - Example: "worldwide box office" → default: ["size"]

# # C. ORDINAL (定序数据):
# #    - Keywords: "rank", "level", "grade", "priority", "order", "sequence"
# #    - Best channels (in priority order):
# #      1. position (natural ordering)
# #      2. size (shows progression)
# #      3. lightness (gradual change)
# #      4. orientation (angle progression)
# #    - Example: "priority level" → default: ["lightness"]

# # D. TEMPORAL (时间数据):
# #    - Keywords: "time", "date", "year", "month", "day", "period", "quarter", "season"
# #    - Best channels:
# #      1. position (standard for time)
# #      2. orientation (circular time like clock)
# #    - Example: "year" → default: ["position"]

# # **Default Strategy if Uncertain:**
# # - If field1 appears more categorical → default: ["color"]
# # - If field2 appears more quantitative → default: ["size"]
# # - If both uncertain → field1: ["color"], field2: ["size"]

# # [Channels Configuration]
# # Both fields must specify:
# # - allowed: The full list of available channels
# # - default: A single-element list ["<channel>"] chosen intelligently based on data semantics above

# # field1.channels:
# #   allowed = ["position","size","lightness","color","texture","orientation","shape"]
# #   default = ["<intelligently chosen for {field1}>"]

# # field2.channels:
# #   allowed = ["position","orientation","lightness","color","texture","size","shape"]
# #   default = ["<intelligently chosen for {field2}>"]

# # [defaultPlan Composition]
# # Compose defaultPlan with EXACTLY TWO rows:
# #   * Row 1 (for field1):
# #       dataField   = "{field1}"
# #       subitemId   = the subitem_id of the FIRST item in field1.subitemOptions
# #       subitemName = the name of that FIRST item
# #       channels    = field1.channels.default
# #   * Row 2 (for field2):
# #       dataField   = "{field2}"
# #       subitemId   = the subitem_id of the FIRST item in field2.subitemOptions
# #       subitemName = the name of that FIRST item
# #       channels    = field2.channels.default

# # IMPORTANT: The first subitem in field1.subitemOptions MUST NOT be the same subitem_id as the first in field2.subitemOptions.
# # If they would otherwise be the same, reorder field2.subitemOptions so its first item is different (membership stays identical).

# # [Inputs]
# # - field(compat): {field}
# # - field1: {field1}
# # - field2: {field2}
# # - keyword: {keyword}
# # - dataFact: {data_fact}
# # - contextDescription: {context_description}

# # [EXAMPLE REASONING]
# # If field1="type" and field2="worldwide":
# # - "type" contains keyword "type" → CATEGORICAL → best channel: color
# #   → field1.channels.default = ["color"]
# # - "worldwide" suggests global revenue → QUANTITATIVE → best channel: size
# #   → field2.channels.default = ["size"]

# # If field1="rank" and field2="year":
# # - "rank" is ORDINAL → best channel: position or lightness
# #   → field1.channels.default = ["position"]
# # - "year" is TEMPORAL → best channel: position
# #   → field2.channels.default = ["position"]
# #   (Both use position but on different axes/subitems)

# # [OUTPUT JSON (keys and hierarchy MUST match exactly)]
# # {{
# #   "mapping_id": "{mapping_id}",
# #   "keyword": "{keyword}",
# #   "dataFact": "{data_fact}",
# #   "contextDescription": "{context_description}",
# #   "defaultPlan": [
# #     {{ "dataField": "{field1}", "subitemId": "<= field1.subitemOptions[0].subitem_id>", "subitemName": "<= that item's name>", "channels": ["<= intelligently chosen>"] }},
# #     {{ "dataField": "{field2}", "subitemId": "<= field2.subitemOptions[0].subitem_id>", "subitemName": "<= that item's name>", "channels": ["<= intelligently chosen>"] }}
# #   ],
# #   "field1": {{
# #     "dataField": "{field1}",
# #     "subitemOptions": [
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
# #     ],
# #     "channels": {{
# #       "allowed":  ["position","size","lightness","color","texture","orientation","shape"],
# #       "default":  ["<single intelligently chosen channel>"]
# #     }}
# #   }},
# #   "field2": {{
# #     "dataField": "{field2}",
# #     "subitemOptions": [
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<English name>", "geometry": "<point|line|area>" }}
# #     ],
# #     "channels": {{
# #       "allowed":  ["position","orientation","lightness","color","texture","size","shape"],
# #       "default":  ["<single intelligently chosen channel>"]
# #     }}
# #   }}
# # }}

# # [STRICT REQUIREMENTS]
# # - Output ONE valid JSON object; no extra text/Markdown.
# # - 3-5 metaphor-specific subitems (not generic names)
# # - defaultPlan MUST contain exactly two rows, one for "{field1}" and one for "{field2}"
# # - defaultPlan rows MUST mirror the FIRST item of each field's subitemOptions and MUST copy the field's channels.default
# # - defaultPlan.subitemId MUST exist in the corresponding field block's subitemOptions; defaultPlan.subitemName MUST equal that subitem's name
# # - All strings MUST be English; geometry ∈ {{point, line, area}}
# # - ✅ DEFAULT CHANNELS MUST BE INTELLIGENTLY CHOSEN based on field semantics and data type detection rules above
# # - Each channels.default must be a single-element array: ["channel_name"]
# # """.strip()

# # 版本v1
# # from typing import Dict, List, Any
# # from ..module2_metaphor_generation.constants import MetaphorMethod

# # from langchain_openai import ChatOpenAI
# # from langchain.schema import HumanMessage, SystemMessage
# # import os
# # import json

# # def llm_generate(prompt: str) -> str:
# #     chat = ChatOpenAI(
# #         model="gpt-4",
# #         temperature=0.4,
# #         openai_api_key=os.getenv("OPENAI_API_KEY"),
# #         openai_api_base=os.getenv("OPENAI_API_BASE", "https://ai-yyds.com/v1")
# #     )

# #     messages = [
# #         SystemMessage(content="你是一个可视化隐喻专家，请根据用户提示生成结构化映射。"),
# #         HumanMessage(content=prompt)
# #     ]

# #     response = chat(messages)
# #     return response.content.strip()


# # class MappingAgent:
# #     def __init__(self):
# #         self.name = "MappingAgent"
    
# #     def run(self, 
# #             field: str,
# #             keyword: str, 
# #             data_fact: str,
# #             method: MetaphorMethod,
# #             context_description: str) -> List[Dict[str, Any]]:
            
# #         """
# #         构建视觉隐喻映射通道
        
# #         Args:
# #             field: 数据字段（本体）
# #             keyword: 喻体关键词
# #             data_fact: 数据特征
# #             method: 隐喻方法（GUIDED/BLIND）
# #             context_description: 上下文描述
            
# #         Returns:
# #             Dict包含映射信息
# #         """
        
# #         # TODO: 实现Agent逻辑
# #         # 1. 根据输入参数构建视觉映射
# #         # 2. 应用预设的映射模板
# #         # 3. 生成2-4个可视觉表现的mapping元素
# #         prompt =self._build_mapping_prompt(field, keyword, data_fact, context_description)
# #         response = llm_generate(prompt)
        
# #         try:
# #             result = json.loads(response)
# #             if isinstance(result, dict):
# #                 result = [result]  # 保证统一为 list
# #             return result
# #         except Exception as e:
# #             print("⚠️ LLM response parsing error:", e)
# #             print("原始响应:", response)
# #             return []
        
# #         # # 临时返回示例数据
# #         # return {
# #         #     "source": field,
# #         #     "target": keyword,
# #         #     "mapping": ["颜色", "尺寸", "明度"]
# #         # }
    
# #     def _build_mapping_prompt(self, field: str, keyword: str, data_fact: str, context_description: str) -> str:
# #         """
# #         构建映射提示词
# #         """
# #         mapping_instruction = f"""
# # 以下是数据字段、本体、喻体及其特征，请基于可视化映射知识构造"数据特征 → 喻体特征"的隐喻映射关系：

# # 本体（数据字段）：{field}
# # 喻体关键词：{keyword}
# # 数据特征：{data_fact}
# # 上下文描述：{context_description}

# # 视觉映射知识
# # - 视觉标记分为：点、线、面；
# # - 视觉通道包括：
# #   - 位置：用于表现数值或结构位置
# #   - 尺寸：表现数量、规模或强度
# #   - 明度：表现等级或程度
# #   - 颜色：常用于趋势或类别
# #   - 方向：表现方向性变化
# #   - 纹理：表现密度、变化频率
# #   - 形状：表现分类、结构差异




# # 输出要求：
# # 请构造 JSON 数组，每个元素包括：
# # - source：本体字段
# # - target：喻体中的某个视觉结构
# # - mapping：用于该结构的 2~4 个视觉通道
# # 请仅返回合法 JSON 数组，不要包含解释文字或 markdown
# # """
# #         return mapping_instruction.strip()


# # 中文版：
# # 请严格按下述规则与输出格式，返回**唯一的JSON对象**（不要解释，不要Markdown）：

# # [任务]
# # - 根据“喻体关键词：{keyword}”自动构造与该喻体语义相关的**视觉标记子项**（3~6个），每个子项必须属于**点/线/面**之一：
# #   - geometry ∈ {{"point","line","area"}}
# #   - 如需表达带状，使用 variant:"band"（仅当 geometry="area" 时可出现）
# # - 基于字段名：field1="{field1}"，field2="{field2}"，生成默认映射方案 defaultPlan（恰好2条）：
# #   - “看起来像时间”的字段（包含 词根：时间/time/date/year/month/day/week）→ 选一个 line 子项 + channels=["position"]
# #   - 另一个字段 → 选一个 area（优先有 variant:"band" 的） + channels=["size"]
# #   - 若两者都像/都不像时间：按顺序 field1→line+position，field2→area(+band)+size
# # - field1 与 field2 的 block 中：
# #   - subitemOptions：列出上面生成的所有子项（id/name/geometry/variant）
# #   - channels：根据 geometry 给出可用/禁用/默认通道（严格七个：position, size, lightness, color, texture, orientation, shape）
# #     * line：allowed=[position,orientation,lightness,color,texture], disabled=[size,shape]
# #     * area：allowed=[position,size,lightness,color,texture,orientation], disabled=[shape]
# #     * point：allowed=[position,size,lightness,color,texture,shape,orientation], disabled=[]
# #   - channels.default 等于 defaultPlan 中该字段当前选中子项的 channels

# # [必须使用的 mapping_id 值]
# # - "{mapping_id}"

# # [输入信息]
# # - field(兼容)：{field}
# # - field1：{field1}
# # - field2：{field2}
# # - keyword：{keyword}
# # - dataFact：{data_fact}
# # - contextDescription：{context_description}

# # [输出JSON格式（键名与层级必须完全一致）]
# # {{
# #   "mapping_id": "{mapping_id}",
# #   "keyword": "{keyword}",
# #   "dataFact": "{data_fact}",
# #   "contextDescription": "{context_description}",
# #   "defaultPlan": [
# #     {{ "dataField": "<= field1或field2之一>", "subitemId": "<= 上述子项之一的subitem_id>", "channels": ["<通道1>", "<可选通道2>"] }},
# #     {{ "dataField": "<= 另一个字段>",         "subitemId": "<= 子项id>",                "channels": ["<通道1>"] }}
# #   ],
# #   "field1": {{
# #     "dataField": "{field1}",
# #     "subitemOptions": [
# #       {{ "subitem_id": "<id>", "name": "<中文名>", "geometry": "<point|line|area>" }},
# #       {{ "subitem_id": "<id>", "name": "<中文名>", "geometry": "<point|line|area>", "variant": "band" }}
# #     ],
# #     "channels": {{
# #       "allowed":  ["position","size","lightness","color","texture","orientation","shape"],
# #       "disabled": ["shape"],
# #       "default":  ["size"]
# #     }}
# #   }},
# #   "field2": {{
# #     "dataField": "{field2}",
# #     "subitemOptions": [ /* 与 field1 使用同一批子项；顺序可不同 */ ],
# #     "channels": {{
# #       "allowed":  ["position","orientation","lightness","color","texture"],
# #       "disabled": ["size","shape"],
# #       "default":  ["position"]
# #     }}
# #   }}
# # }}

# # [严格要求]
# # - 只能返回一个JSON对象，不能有多余文字/代码块。
# # - geometry 仅能是 point/line/area；variant 仅能省略或为 "band"。
# # - 所有通道名必须来自七个固定通道之一。
# # - defaultPlan 的 subitemId 必须在 subitemOptions 里出现。
# # - field1/field2 的 channels.default 必须与 defaultPlan 对应字段的 channels 保持一致。