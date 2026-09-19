# """
# 共享的映射决策逻辑
# 确保Agent6和Agent7使用相同的映射选择策略
# """

# from typing import Dict, List, Tuple, Optional
# import os
# from langchain_openai import ChatOpenAI
# from langchain.schema import HumanMessage, SystemMessage
# import json
# import re


# # 定义标准视觉通道
# STANDARD_CHANNELS = {
#     'position': ['position', 'x', 'y', 'position on x-axis', 'position on y-axis', 'location'],
#     'size': ['size', 'area', 'radius', 'width', 'height'],
#     'color': ['color', 'hue', 'colour'],
#     'lightness': ['lightness', 'brightness', 'value', 'luminance'],
#     'texture': ['texture', 'pattern'],
#     'orientation': ['orientation', 'angle', 'rotation'],
#     'shape': ['shape', 'form', 'mark type']
# }


# def normalize_channel(channel: str) -> str:
#     """将非标准channel名称规范化为标准名称"""
#     channel_lower = channel.lower().strip()
    
#     for standard, variations in STANDARD_CHANNELS.items():
#         if channel_lower in variations:
#             return standard
    
#     # 如果找不到匹配，返回原值（会被后续过滤）
#     print(f"⚠️ 未识别的channel: {channel}")
#     return channel_lower


# def validate_and_fix_mapping(mapping: Dict, field_name: str) -> Dict:
#     """
#     验证并修复映射决策
#     - 确保只有一个主要channel
#     - 规范化channel名称
#     """
#     channels = mapping.get("channels", [])
    
#     # 规范化所有channels
#     normalized = [normalize_channel(ch) for ch in channels]
    
#     # 过滤掉无效的channels
#     valid_channels = [ch for ch in normalized if ch in STANDARD_CHANNELS.keys()]
    
#     if not valid_channels:
#         # 如果没有有效channel，根据字段类型给默认值
#         print(f"⚠️ {field_name}: 无有效channel，使用默认值")
#         valid_channels = ['color']  # 默认使用color
    
#     # 只保留第一个channel（优先级最高的）
#     primary_channel = valid_channels[0]
    
#     if len(valid_channels) > 1:
#         print(f"⚠️ {field_name}: 多个channels {valid_channels}，只保留主要的 '{primary_channel}'")
    
#     # 更新映射
#     mapping["channels"] = [primary_channel]
    
#     return mapping


# def get_shared_mapping_decision(
#     keyword: str,
#     field1: str,
#     field2: str,
#     data_fact: str,
#     context_description: str,
#     subitems: Optional[List[Dict]] = None
# ) -> Dict:
#     """
#     核心函数：决定最佳的subitem-channel映射
#     """
    
#     try:
#         llm = ChatOpenAI(
#             model="gpt-4o-mini",
#             temperature=0.3,
#             openai_api_key=os.getenv("OPENAI_API_KEY"),
#             openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
#         )
        
#         # 构建subitems上下文
#         subitems_context = ""
#         if subitems:
#             subitems_list = "\n".join([
#                 f"- {s['name']} ({s['geometry']})"
#                 for s in subitems
#             ])
#             subitems_context = f"""
# Available subitems:
# {subitems_list}

# Choose from the above subitems.
# """
        
#         prompt = f"""
# You are a visual metaphor expert. Decide the BEST mapping between data dimensions and visual elements.

# Context:
# - Metaphor: {keyword}
# - Data dimension 1: {field1}
# - Data dimension 2: {field2}
# - Data insight: {data_fact}
# - Dataset: {context_description}

# {subitems_context}

# CRITICAL RULES:
# 1. Each data field maps to EXACTLY ONE primary visual channel
# 2. Use ONLY these standard channels: position, size, color, lightness, texture, orientation, shape
# 3. Common mappings:
#    - Categorical data → color, shape, texture
#    - Quantitative data → position, size, lightness, orientation
#    - Temporal data → position
# 4. Choose the MOST INTUITIVE channel for each field
# 5. Visual intuitiveness: Natural mapping (size for quantity, color for category, position for time)
# 6. Metaphor coherence: Use semantically meaningful parts
# 7. Visual clarity: Avoid cluttered encodings
# 8. Aesthetic quality: Create beautiful visualizations

# Return JSON only:
# {{
#   "field1_mapping": {{
#     "subitem_name": "<part name>",
#     "geometry": "point|line|area",
#     "channels": ["<ONE standard channel>"],
#     "rationale": "<why this specific channel>"
#   }},
#   "field2_mapping": {{
#     "subitem_name": "<part name>",
#     "geometry": "point|line|area", 
#     "channels": ["<ONE standard channel>"],
#     "rationale": "<why this specific channel>"
#   }},
#   "overall_reasoning": "<how they work together>"
# }}

# EXAMPLE:
# {{
#   "field1_mapping": {{
#     "subitem_name": "petal",
#     "geometry": "area",
#     "channels": ["color"],
#     "rationale": "Color effectively shows categorical differences"
#   }},
#   "field2_mapping": {{
#     "subitem_name": "petal",
#     "geometry": "area",
#     "channels": ["size"],
#     "rationale": "Size naturally represents magnitude"
#   }}
# }}
# """

#         response = llm.invoke([
#             SystemMessage(content="You are an expert in data visualization. Return only valid JSON with ONE channel per field."),
#             HumanMessage(content=prompt)
#         ])
        
#         # 解析响应
#         result_text = response.content.strip()
#         result_text = re.sub(r'```json\s*', '', result_text)
#         result_text = re.sub(r'```\s*', '', result_text)
#         result_text = result_text.strip()
        
#         result = json.loads(result_text)
        
#         # 验证和修复映射
#         result["field1_mapping"] = validate_and_fix_mapping(result["field1_mapping"], field1)
#         result["field2_mapping"] = validate_and_fix_mapping(result["field2_mapping"], field2)
        
#         print("=" * 80)
#         print("🎯 共享映射决策结果:")
#         print(f"  {field1} → {result['field1_mapping']['subitem_name']} ({result['field1_mapping']['channels'][0]})")
#         print(f"  {field2} → {result['field2_mapping']['subitem_name']} ({result['field2_mapping']['channels'][0]})")
#         print(f"  理由: {result.get('overall_reasoning', '')[:100]}...")
#         print("=" * 80)
        
#         return result
        
#     except Exception as e:
#         print(f"⚠️ 映射决策失败: {e}")
#         # 返回合理的默认值
#         return {
#             "field1_mapping": {
#                 "subitem_name": "main element",
#                 "geometry": "area",
#                 "channels": ["color"],
#                 "rationale": "Default categorical encoding"
#             },
#             "field2_mapping": {
#                 "subitem_name": "main element", 
#                 "geometry": "area",
#                 "channels": ["size"],
#                 "rationale": "Default quantitative encoding"
#             },
#             "overall_reasoning": "Using default mappings"
#         }


# def extract_mapping_from_prompt(image_prompt: str) -> Dict:
#     """
#     从Agent7生成的prompt中提取实际使用的映射关系
#     """
#     try:
#         llm = ChatOpenAI(
#             model="gpt-4o-mini",
#             temperature=0.1,
#             openai_api_key=os.getenv("OPENAI_API_KEY"),
#             openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
#         )
        
#         analysis_prompt = f"""
# Analyze this image generation prompt and extract the data-to-visual mappings.

# Prompt:
# {image_prompt}

# Return JSON only:
# {{
#   "mappings": [
#     {{
#       "data_field": "<field name>",
#       "visual_element": "<metaphor part>",
#       "channels": ["<channels>"]
#     }}
#   ]
# }}
# """
        
#         response = llm.invoke([
#             SystemMessage(content="Extract mapping information from visualization prompts."),
#             HumanMessage(content=analysis_prompt)
#         ])
        
#         result_text = response.content.strip()
#         result_text = re.sub(r'```json\s*', '', result_text)
#         result_text = re.sub(r'```\s*', '', result_text)
        
#         extracted = json.loads(result_text)
#         print("🔍 从prompt提取的映射:", extracted)
#         return extracted
        
#     except Exception as e:
#         print(f"⚠️ 映射提取失败: {e}")
#         return {"mappings": []}


# v1:缺乏规范的映射
"""
共享的映射决策逻辑
确保Agent6和Agent7使用相同的映射选择策略
"""

from typing import Dict, List, Tuple, Optional
import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
import re


def get_shared_mapping_decision(
    keyword: str,
    field1: str,
    field2: str,
    data_fact: str,
    context_description: str,
    subitems: Optional[List[Dict]] = None
) -> Dict:
    """
    核心函数：决定最佳的subitem-channel映射
    
    Args:
        keyword: 隐喻关键词（如flower, tree等）
        field1: 第一个数据维度
        field2: 第二个数据维度
        data_fact: 数据洞察
        context_description: 数据集上下文
        subitems: 可选的子项列表
        
    Returns:
        {
            "field1_mapping": {
                "subitem_name": "petal",
                "geometry": "area", 
                "channels": ["color"]
            },
            "field2_mapping": {
                "subitem_name": "petal",
                "geometry": "area",
                "channels": ["size"]
            },
            "overall_reasoning": "理由说明..."
        }
    """
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
        )
        
        # 构建subitems上下文
        subitems_context = ""
        if subitems:
            subitems_list = "\n".join([
                f"- {s['name']} ({s['geometry']})"
                for s in subitems
            ])
            subitems_context = f"""
Available subitems:
{subitems_list}

Choose from the above subitems.
"""
        
        prompt = f"""
You are a visual metaphor expert. Decide the BEST mapping between data dimensions and visual elements.

Context:
- Metaphor: {keyword}
- Data dimension 1: {field1}
- Data dimension 2: {field2}
- Data insight: {data_fact}
- Dataset: {context_description}

{subitems_context}

Your goal: Choose the most INTUITIVE and EFFECTIVE mapping that will create a beautiful, understandable visualization.Each data field maps to ONE primary visual channel.

Key principles:
1. Visual Intuitiveness: The mapping should feel natural (e.g., size for quantity, color for category)
2. Metaphor Coherence: Use parts of {keyword} that make semantic sense
3. Visual Clarity: Avoid mappings that would create visual clutter or confusion
4. Aesthetic Quality: Consider how this will look as a final illustration
5.choose from these channels: position, size, color, lightness, texture, orientation, shape
- Categorical data → color, shape, texture
- Quantitative data → position, size, lightness, orientation
- Temporal data → position

Think step by step:
1. What is the data type of {field1}? (categorical/quantitative/temporal/ordinal)
2. What is the data type of {field2}? 
3. Which parts of {keyword} are most visually prominent and flexible?
4. What channel best represents each data dimension while creating visual harmony?

Return JSON only:
{{
  "field1_mapping": {{
    "subitem_name": "<part name>",
    "geometry": "point|line|area",
    "channels": ["<channel>"],
    "rationale": "<why>"
  }},
  "field2_mapping": {{
    "subitem_name": "<part name>",
    "geometry": "point|line|area", 
    "channels": ["<channel>"],
    "rationale": "<why>"
  }},
  "overall_reasoning": "<how they work together>"
}}
"""

        response = llm.invoke([
            SystemMessage(content="You are an expert in data visualization. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # 解析响应
        result_text = response.content.strip()
        result_text = re.sub(r'```json\s*', '', result_text)
        result_text = re.sub(r'```\s*', '', result_text)
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        print("=" * 80)
        print("🎯 共享映射决策结果:")
        print(f"  {field1} → {result['field1_mapping']['subitem_name']} ({result['field1_mapping']['channels']})")
        print(f"  {field2} → {result['field2_mapping']['subitem_name']} ({result['field2_mapping']['channels']})")
        print(f"  理由: {result.get('overall_reasoning', '')[:100]}...")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"⚠️ 映射决策失败: {e}")
        # 返回合理的默认值
        return {
            "field1_mapping": {
                "subitem_name": "main element",
                "geometry": "area",
                "channels": ["color"],
                "rationale": "Default categorical encoding"
            },
            "field2_mapping": {
                "subitem_name": "main element", 
                "geometry": "area",
                "channels": ["size"],
                "rationale": "Default quantitative encoding"
            },
            "overall_reasoning": "Using default mappings"
        }


def extract_mapping_from_prompt(image_prompt: str) -> Dict:
    """
    从Agent7生成的prompt中提取实际使用的映射关系
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
        )
        
        analysis_prompt = f"""
Analyze this image generation prompt and extract the data-to-visual mappings.

Prompt:
{image_prompt}

Return JSON only:
{{
  "mappings": [
    {{
      "data_field": "<field name>",
      "visual_element": "<metaphor part>",
      "channels": ["<channels>"]
    }}
  ]
}}
"""
        
        response = llm.invoke([
            SystemMessage(content="Extract mapping information from visualization prompts."),
            HumanMessage(content=analysis_prompt)
        ])
        
        result_text = response.content.strip()
        result_text = re.sub(r'```json\s*', '', result_text)
        result_text = re.sub(r'```\s*', '', result_text)
        
        extracted = json.loads(result_text)
        print("🔍 从prompt提取的映射:", extracted)
        return extracted
        
    except Exception as e:
        print(f"⚠️ 映射提取失败: {e}")
        return {"mappings": []}


