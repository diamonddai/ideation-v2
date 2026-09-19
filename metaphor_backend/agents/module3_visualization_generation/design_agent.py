# v3

# agent7.py 
from typing import Dict, Any
import os, json
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import re

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
    chat = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1"),
    )
    system_message = SystemMessage(content="""你是一位专业的视觉隐喻设计师。
你的任务是基于提供的数据映射规范，生成高质量的图像提示词。
你应该忠实地使用规范中的映射关系，同时保持创作自由度以确保视觉效果。""")
    return chat([system_message, HumanMessage(content=prompt)]).content.strip()


def build_prompt0_v5_guided(mapping_spec: Dict[str, Any]) -> str:
    """
    基于mapping_spec的defaultPlan生成prompt
    保持创作自由度，但明确使用指定的映射关系
    """
    
    keyword = mapping_spec.get("keyword", "")
    data_fact = mapping_spec.get("dataFact", "")
    context_description = mapping_spec.get("contextDescription", "")
    default_plan = mapping_spec.get("defaultPlan", [])
    
    # ✅ 从defaultPlan中提取映射关系（这已经是最佳选择了）
    mapping_guidance = ""
    if len(default_plan) >= 2:
        row1 = default_plan[0]
        row2 = default_plan[1]
        
        field1_name = row1.get("dataField", "")
        field1_subitem = row1.get("subitemName", "")
        field1_channels = ", ".join(row1.get("channels", []))
        
        field2_name = row2.get("dataField", "")
        field2_subitem = row2.get("subitemName", "")
        field2_channels = ", ".join(row2.get("channels", []))
        
        mapping_guidance = f"""
📊 DATA-TO-VISUAL MAPPING (Follow this as your core structure):
First mapping:
- Data dimension "{field1_name}" → Use {keyword}'s "{field1_subitem}" 
  Visual encoding: {field1_channels}
  
second mapping:
- Data dimension "{field2_name}" → Use {keyword}'s "{field2_subitem}"
  Visual encoding: {field2_channels}

These mappings have been carefully selected for optimal visual communication.
Your prompt should naturally incorporate these mappings while maintaining artistic quality.
"""

    design_philosophy = """
🎨 DESIGN PHILOSOPHY:Modern Information Design with Poetic Visual Metaphors

一、从抽象到具象
- 将{keyword}转化为可识别的具体物体或场景
- Use the actual form of the metaphor as the visualization structure
- 保留物体的自然形态，通过其属性编码数据,Recognizable metaphorical objects that encode data naturally
- Balance between aesthetic beauty and data clarity
- Decorative elements support (not distract from) data understanding
- Data encodings should feel intuitive and natural
- 例如：tree→真实的树形，ocean→可见的波浪形态，river→蜿蜒的河流

二、视觉风格参考
- Modern editorial illustration style with data storytelling(like New York Times / The Economist infographics)
- Flat design with subtle depth 
- Hand-crafted digital aesthetic
- Sophisticated color palettes (not limited to primary colors)

三、色彩策略
- Primary: Based on the metaphor's natural appearance
- Secondary: Complementary or analogous for harmony  
- Accent: For data highlights (can be vibrant)
- Background: Soft neutrals (beige, pale gray, cream, etc.)

四、构图原则
- Consider golden ratio or rule of thirds
- Create clear visual focal points
- Ensure readability without being overly sparse

五、数据编码方式
- Categorical data → color, shape, texture
- Quantitative data → position, size, lightness, orientation
- Temporal data → position

六、细节与装饰
- 适度的装饰元素增强理解
- 注释可以优雅地融入设计

七、风格关键词
- Editorial illustration
- Infographic design
- Data storytelling
- Modern vintage aesthetic
- Sophisticated minimalism
- Narrative visualization
- Organic data forms

八、避免
- 过度抽象的纯几何形状
- 生硬的网格和直线（除非数据本身需要）
- 单调的原色块
- 缺乏故事性的纯数据展示
"""

    prompt = f"""
Create a sophisticated data visualization using the metaphor of "{keyword}".

{mapping_guidance}

Context:
- Data Insight: {data_fact}
- Dataset Description: {context_description}

{design_philosophy}

Your Task:
Generate a detailed, professional image generation prompt that:
1. Faithfully uses the specified data-to-visual mappings above
2. Creates a beautiful, magazine-quality illustration
3. Balances data clarity with aesthetic appeal
4. Results in an image that would work well in a data journalism context

Style Keywords to Include:
- Editorial illustration style
- Modern infographic design  
- Data storytelling aesthetic
- Sophisticated color palette
- Clean composition with purposeful detail

IMPORTANT: 
- Your prompt should naturally incorporate the specified mappings
- Maintain creative freedom in visual details and style choices
- Focus on creating a prompt that will generate a HIGH-QUALITY image
- The result should be both informative and visually striking

Output the complete image generation prompt directly (no JSON wrapper needed).
"""

    return prompt.strip()


class DesignAgent:
    """Agent7：图像提示词生成器
    """
    
    def __init__(self):
        self.name = "DesignAgent"
        self.use_v5_mode = os.getenv("AGENT7_USE_V5_MODE", "true").lower() in ("1", "true", "yes")

    def _run_v5_mode(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
        """v5模式：基于最佳映射生成高质量prompt"""
        try:
            # ✅ 使用改进的prompt构建器
            prompt0 = build_prompt0_v5_guided(mapping_spec)
            
            prompt1_raw = llm_generate(prompt0)
            
            # 清理prompt1
            prompt1 = re.sub(r'<think>.*?</think>', '', prompt1_raw, flags=re.DOTALL)
            
            # 尝试提取反引号包围的内容
            match = re.search(r'`([^`]+)`', prompt1)
            if match:
                prompt1 = match.group(1).strip()
            else:
                # 如果没有反引号，使用整个清理后的文本
                # 移除可能的markdown标记
                prompt1 = prompt1.strip()
                # 如果文本太短，可能解析出了问题，使用原始响应
                if len(prompt1) < 50:
                    prompt1 = prompt1_raw.strip()
            
            print("=" * 80)
            print("✅ Agent7 生成的图像提示词:")
            print(prompt1[:200] + "..." if len(prompt1) > 200 else prompt1)
            print("=" * 80)
            
            # 验证prompt中是否包含了关键映射信息
            default_plan = mapping_spec.get("defaultPlan", [])
            if len(default_plan) >= 2:
                row1_subitem = default_plan[0].get("subitemName", "")
                row2_subitem = default_plan[1].get("subitemName", "")
                
                # 简单检查（不要太严格）
                if row1_subitem.lower() in prompt1.lower() or row2_subitem.lower() in prompt1.lower():
                    print(f"✅ Prompt包含了映射的subitem: {row1_subitem}, {row2_subitem}")
                else:
                    print(f"⚠️  Prompt可能未明确包含subitem名称，但这可能是自然的变体表达")
            
            if prompt1:
                return {
                    "mapping_id": mapping_spec.get("mapping_id"),
                    "keyword": mapping_spec.get("keyword"),
                    "dataFact": mapping_spec.get("dataFact"),
                    "contextDescription": mapping_spec.get("contextDescription", ""),
                    "prompt_lines": [prompt1],
                    "image_prompt": prompt1,
                    "data_fact_caption": mapping_spec.get("contextDescription") or f"{mapping_spec.get('keyword', '数据')}呈现{mapping_spec.get('dataFact', '趋势')}特征",
                    "v5_metadata": {
                        "version": "v5_guided_mapping",
                        "mode": "balanced_fidelity_and_creativity",
                        "mapping_enforced": True
                    }
                }
            else:
                return self._run_template_mode(mapping_spec)
                
        except Exception as e:
            print(f"v5模式失败，回退到模板模式: {e}")
            import traceback
            traceback.print_exc()
            return self._run_template_mode(mapping_spec)

    def _build_prompt(self, mapping_spec: Dict[str, Any]) -> str:
        """模板模式的prompt构建（保持不变）"""
        a6 = json.dumps(mapping_spec, ensure_ascii=False)
        return f"""
你将收到一个来自 Agent6 的 JSON（mapping_spec）。请基于其中的字段生成"固定5句"的英文提示词数组（prompt_lines），以及合并后的 image_prompt。
严格要求：
- 只输出**一个**JSON对象，不要额外文字/Markdown。
- 使用**固定5句模板**...

【mapping_spec】
{a6}

【输出JSON的**唯一**格式】
{{
  "mapping_id": "<复制 mapping_spec.mapping_id>",
  "keyword": "<复制 mapping_spec.keyword>",
  "dataFact": "<复制 mapping_spec.dataFact>",
  "contextDescription": "<复制 mapping_spec.contextDescription>",
  "prompt_lines": ["S1","S2","S3","S4","S5"],
  "image_prompt": "<S1 S2 S3 S4 S5 的拼接>",
  "data_fact_caption": "<中文一句话>"
}}
""".strip()

    def _run_template_mode(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
        """模板模式（保持不变）"""
        prompt = self._build_prompt(mapping_spec)
        raw = llm_generate(prompt)
        if "```" in raw:
            raw = raw.split("```")[-2] if raw.count("```") >= 2 else raw.replace("```", "")
        raw = raw.strip()
        try:
            return clean_json_response(raw)
        except Exception as e:
            error_msg = f"DesignAgent failed to parse LLM response: {str(e)}"
            print(error_msg)
            print(f"Raw response (first 500 chars): {raw[:500]}")
            raise ValueError(error_msg)

    def run(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
        """主运行函数"""
        if self.use_v5_mode:
            return self._run_v5_mode(mapping_spec)
        else:
            return self._run_template_mode(mapping_spec)


# # agent7.py - v2改进版
# from typing import Dict, Any
# import os, json
# from langchain_openai import ChatOpenAI
# from langchain.schema import HumanMessage, SystemMessage
# import re

# def clean_json_response(text: str) -> dict:
#     """清理LLM响应并解析JSON"""
#     text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
#     text = re.sub(r'<[^>]+>', '', text)
#     text = text.strip()
    
#     if '```json' in text:
#         match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
#         if match:
#             text = match.group(1)
#     elif '```' in text:
#         match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
#         if match:
#             text = match.group(1)
    
#     start_idx = text.find('{')
#     end_idx = text.rfind('}')
    
#     if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
#         text = text[start_idx:end_idx + 1]
    
#     return json.loads(text)

# def llm_generate(prompt: str) -> str:
#     chat = ChatOpenAI(
#         model="gpt-4o-mini",
#         temperature=0.4,
#         openai_api_key=os.getenv("OPENAI_API_KEY"),
#         openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1"),
#     )
#     system_message = SystemMessage(content="""你是一位专业的视觉隐喻设计师。
# 你的任务是基于提供的数据映射规范，生成高质量的图像提示词。
# 你应该忠实地使用规范中的映射关系，同时保持创作自由度以确保视觉效果。""")
#     return chat([system_message, HumanMessage(content=prompt)]).content.strip()


# def build_prompt0_v5_guided(mapping_spec: Dict[str, Any]) -> str:
#     """
#     v5改进版：基于mapping_spec的defaultPlan生成prompt
#     保持创作自由度，但明确使用指定的映射关系
#     """
    
#     keyword = mapping_spec.get("keyword", "")
#     data_fact = mapping_spec.get("dataFact", "")
#     context_description = mapping_spec.get("contextDescription", "")
#     default_plan = mapping_spec.get("defaultPlan", [])
    
#     # ✅ 从defaultPlan中提取映射关系（这已经是最佳选择了）
#     mapping_guidance = ""
#     if len(default_plan) >= 2:
#         row1 = default_plan[0]
#         row2 = default_plan[1]
        
#         field1_name = row1.get("dataField", "")
#         field1_subitem = row1.get("subitemName", "")
#         field1_channels = ", ".join(row1.get("channels", []))
        
#         field2_name = row2.get("dataField", "")
#         field2_subitem = row2.get("subitemName", "")
#         field2_channels = ", ".join(row2.get("channels", []))
        
#         mapping_guidance = f"""
# 📊 DATA-TO-VISUAL MAPPING (Follow this as your core structure):

# First mapping:
# - Data dimension "{field1_name}" → Use {keyword}'s "{field1_subitem}" 
#   Visual encoding: {field1_channels}
  
# second mapping:
# - Data dimension "{field2_name}" → Use {keyword}'s "{field2_subitem}"
#   Visual encoding: {field2_channels}

# These mappings have been carefully selected for optimal visual communication.
# Your prompt should naturally incorporate these mappings while maintaining artistic quality.
# """

#     design_philosophy = """
# 🎨 DESIGN PHILOSOPHY:Modern Information Design with Poetic Visual Metaphors


# Style: Modern editorial illustration with data storytelling
# - Think New York Times / The Economist infographics
# - Recognizable metaphorical objects that encode data naturally
# - Balance between aesthetic beauty and data clarity

# Visual Approach:
# - Use the actual form of the metaphor as the visualization structure
# - Apply sophisticated color palettes (not limited to primary colors)
# - Include subtle depth through layering, transparency, or gradients

# Key Principles:
# 1. The metaphor should be immediately recognizable
# 2. Data encodings should feel intuitive and natural
# 3. Visual hierarchy guides the eye to insights
# 4. Decorative elements support (not distract from) data understanding

# Color Strategy:
# - Primary: Based on the metaphor's natural appearance
# - Secondary: Complementary or analogous for harmony  
# - Accent: For data highlights (can be vibrant)
# - Background: Soft neutrals (beige, pale gray, cream, etc.)

# Composition:
# - Consider golden ratio or rule of thirds
# - Create clear visual focal points
# - Use size, overlap, and transparency for depth
# - Ensure readability without being overly sparse
# """

#     prompt = f"""
# Create a sophisticated data visualization using the metaphor of "{keyword}".

# {mapping_guidance}

# Context:
# - Data Insight: {data_fact}
# - Dataset Description: {context_description}

# {design_philosophy}

# Your Task:
# Generate a detailed, professional image generation prompt that:
# 1. Faithfully uses the specified data-to-visual mappings above
# 2. Creates a beautiful, magazine-quality illustration
# 3. Balances data clarity with aesthetic appeal
# 4. Results in an image that would work well in a data journalism context

# Style Keywords to Include:
# - Editorial illustration style
# - Modern infographic design  
# - Data storytelling aesthetic
# - Sophisticated color palette
# - Clean composition with purposeful detail

# IMPORTANT: 
# - Your prompt should naturally incorporate the specified mappings
# - Maintain creative freedom in visual details and style choices
# - Focus on creating a prompt that will generate a HIGH-QUALITY image
# - The result should be both informative and visually striking

# Output the complete image generation prompt directly (no JSON wrapper needed).
# """

#     return prompt.strip()


# class DesignAgent:
#     """Agent7：图像提示词生成器（v2改进版）
    
#     核心改进：
#     1. 忠实使用Agent6的mapping决策（因为已经是最佳选择）
#     2. 保持v5模式的创作自由度
#     3. 支持用户调整映射时的严格模式
#     """
    
#     def __init__(self):
#         self.name = "DesignAgent"
#         self.use_v5_mode = os.getenv("AGENT7_USE_V5_MODE", "true").lower() in ("1", "true", "yes")

#     def _run_v5_mode(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#         """v5模式：基于最佳映射生成高质量prompt"""
#         try:
#             # ✅ 使用改进的prompt构建器
#             prompt0 = build_prompt0_v5_guided(mapping_spec)
            
#             prompt1_raw = llm_generate(prompt0)
            
#             # 清理prompt1
#             prompt1 = re.sub(r'<think>.*?</think>', '', prompt1_raw, flags=re.DOTALL)
            
#             # 尝试提取反引号包围的内容
#             match = re.search(r'`([^`]+)`', prompt1)
#             if match:
#                 prompt1 = match.group(1).strip()
#             else:
#                 # 如果没有反引号，使用整个清理后的文本
#                 # 移除可能的markdown标记
#                 prompt1 = prompt1.strip()
#                 # 如果文本太短，可能解析出了问题，使用原始响应
#                 if len(prompt1) < 50:
#                     prompt1 = prompt1_raw.strip()
            
#             print("=" * 80)
#             print("✅ Agent7 生成的图像提示词:")
#             print(prompt1[:200] + "..." if len(prompt1) > 200 else prompt1)
#             print("=" * 80)
            
#             # 验证prompt中是否包含了关键映射信息
#             default_plan = mapping_spec.get("defaultPlan", [])
#             if len(default_plan) >= 2:
#                 row1_subitem = default_plan[0].get("subitemName", "")
#                 row2_subitem = default_plan[1].get("subitemName", "")
                
#                 # 简单检查（不要太严格）
#                 if row1_subitem.lower() in prompt1.lower() or row2_subitem.lower() in prompt1.lower():
#                     print(f"✅ Prompt包含了映射的subitem: {row1_subitem}, {row2_subitem}")
#                 else:
#                     print(f"⚠️  Prompt可能未明确包含subitem名称，但这可能是自然的变体表达")
            
#             if prompt1:
#                 return {
#                     "mapping_id": mapping_spec.get("mapping_id"),
#                     "keyword": mapping_spec.get("keyword"),
#                     "dataFact": mapping_spec.get("dataFact"),
#                     "contextDescription": mapping_spec.get("contextDescription", ""),
#                     "prompt_lines": [prompt1],
#                     "image_prompt": prompt1,
#                     "data_fact_caption": mapping_spec.get("contextDescription") or f"{mapping_spec.get('keyword', '数据')}呈现{mapping_spec.get('dataFact', '趋势')}特征",
#                     "v5_metadata": {
#                         "version": "v5_guided_mapping",
#                         "mode": "balanced_fidelity_and_creativity",
#                         "mapping_enforced": True
#                     }
#                 }
#             else:
#                 return self._run_template_mode(mapping_spec)
                
#         except Exception as e:
#             print(f"v5模式失败，回退到模板模式: {e}")
#             import traceback
#             traceback.print_exc()
#             return self._run_template_mode(mapping_spec)

#     def _build_prompt(self, mapping_spec: Dict[str, Any]) -> str:
#         """模板模式的prompt构建（保持不变）"""
#         a6 = json.dumps(mapping_spec, ensure_ascii=False)
#         return f"""
# 你将收到一个来自 Agent6 的 JSON（mapping_spec）。请基于其中的字段生成"固定5句"的英文提示词数组（prompt_lines），以及合并后的 image_prompt。
# 严格要求：
# - 只输出**一个**JSON对象，不要额外文字/Markdown。
# - 使用**固定5句模板**...

# 【mapping_spec】
# {a6}

# 【输出JSON的**唯一**格式】
# {{
#   "mapping_id": "<复制 mapping_spec.mapping_id>",
#   "keyword": "<复制 mapping_spec.keyword>",
#   "dataFact": "<复制 mapping_spec.dataFact>",
#   "contextDescription": "<复制 mapping_spec.contextDescription>",
#   "prompt_lines": ["S1","S2","S3","S4","S5"],
#   "image_prompt": "<S1 S2 S3 S4 S5 的拼接>",
#   "data_fact_caption": "<中文一句话>"
# }}
# """.strip()

#     def _run_template_mode(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#         """模板模式（保持不变）"""
#         prompt = self._build_prompt(mapping_spec)
#         raw = llm_generate(prompt)
#         if "```" in raw:
#             raw = raw.split("```")[-2] if raw.count("```") >= 2 else raw.replace("```", "")
#         raw = raw.strip()
#         try:
#             return clean_json_response(raw)
#         except Exception as e:
#             error_msg = f"DesignAgent failed to parse LLM response: {str(e)}"
#             print(error_msg)
#             print(f"Raw response (first 500 chars): {raw[:500]}")
#             raise ValueError(error_msg)

#     def run(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#         """主运行函数"""
#         if self.use_v5_mode:
#             return self._run_v5_mode(mapping_spec)
#         else:
#             return self._run_template_mode(mapping_spec)


# # v2
# # agent7.py  —— LLM 版（极简）
# from typing import Dict, Any
# import os, json
# from langchain_openai import ChatOpenAI
# from langchain.schema import HumanMessage, SystemMessage
# import re  # 在顶部添加

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
#         model="gpt-4o-mini",
#         temperature=0.4,
#         openai_api_key=os.getenv("OPENAI_API_KEY"),
#         openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1"),
#     )
#         # 使用v5实验版本的系统消息
#     system_message = SystemMessage(content="""你是一位专业的视觉隐喻设计师，专门负责将抽象的数据概念转换为精确的视觉隐喻提示词。

# 你的核心任务：
# 1. 深度理解输入数据：
#    - keyword: 数据表中的核心字段，这是隐喻的载体
#    - dataFact: 必须体现的关键数据事实，这是隐喻要传达的核心信息
#    - contextDescription: 数据表的整体背景和上下文描述
#    - defaultPlan: 严格遵循的数据维度与视觉映射通道规范

# 2. 严格遵循v5设计原则：隐喻为结构，数据表达趋势，装饰最少

# 3. 生成高质量的prompt1，确保可直接用于文生图API调用

# 输出标准：
# - 生成完整、精确、可直接使用的prompt1
# - 严格遵循v5设计原则
# - 使用专业、清晰的英文表达
# - 确保隐喻结构与数据映射关系明确""")
#     return chat([system_message, HumanMessage(content=prompt)]).content.strip()

# # ==================== Prompt构建器 ====================
# # # #优化版本
# # def build_prompt0_v5(input_data: Dict[str, Any]) -> str:
# #     """
# #     v5改进版：强制LLM遵循defaultPlan的映射规范
# #     """
    
# #     keyword = input_data.get("keyword", "")
# #     data_fact = input_data.get("dataFact", "")
# #     context_description = input_data.get("contextDescription", "")
# #     default_plan = input_data.get("defaultPlan", [])
    
# #     # ✅ 解析defaultPlan，提取关键映射信息
# #     mapping_instructions = ""
# #     if default_plan and len(default_plan) >= 2:
# #         row1 = default_plan[0]
# #         row2 = default_plan[1]
        
# #         field1_name = row1.get("dataField", "dimension1")
# #         field1_subitem = row1.get("subitemName", "element")
# #         field1_channels = ", ".join(row1.get("channels", ["size"]))
        
# #         field2_name = row2.get("dataField", "dimension2")
# #         field2_subitem = row2.get("subitemName", "element")
# #         field2_channels = ", ".join(row2.get("channels", ["position"]))
        
# #         mapping_instructions = f"""
# # **CRITICAL MAPPING REQUIREMENTS (MUST FOLLOW EXACTLY):**

# # Your visualization MUST encode data using this exact mapping:

# # 1. **{field1_name}** data → Encoded using the **{field1_subitem}** through **{field1_channels}** channel
# #    - Example: If {field1_channels} is "color", different {field1_name} values should have different colors
# #    - Example: If {field1_channels} is "size", different {field1_name} values should have different sizes

# # 2. **{field2_name}** data → Encoded using the **{field2_subitem}** through **{field2_channels}** channel
# #    - Example: If {field2_channels} is "position", different {field2_name} values should be at different positions
# #    - Example: If {field2_channels} is "size", different {field2_name} values should have different sizes

# # **Important Notes:**
# # - The subitems ({field1_subitem} and {field2_subitem}) can be the SAME physical element
# # - But they use DIFFERENT visual channels to encode DIFFERENT data dimensions
# # - Your prompt MUST explicitly describe how each channel encodes its corresponding data field
# # """
    
# #     # 新的设计原则：强调具象隐喻和视觉叙事
# #     fixed_requirements = """
# # DESIGN PHILOSOPHY: Modern Information Design with Poetic Visual Metaphors

# # 一、核心转变：从抽象到具象
# # - 将[metaphor_keyword]转化为可识别的具体物体或场景
# # - 保留物体的自然形态，通过其属性编码数据
# # - 例如：tree→真实的树形，ocean→可见的波浪形态，river→蜿蜒的河流

# # 二、视觉风格参考
# # - Modern editorial illustration style (像《纽约时报》《经济学人》的信息图)
# # - Flat design with subtle depth (扁平但有层次)
# # - Hand-crafted digital aesthetic (数字手绘感)
# # - Sophisticated color palettes (不限于原色，可用渐变)

# # 三、数据编码方式（必须严格遵循上面的MAPPING REQUIREMENTS）
# # - 明确说明哪个视觉通道编码哪个数据维度
# # - 不要模糊或隐喻性地描述，要直接说明映射关系
# # - position适合编码类别，定序或定量的数据
# # - color适合编码类别数据
# # - lightness适合编码定序或定量的数据
# # - size适合编码定序或定量的数据
# # - orientation方向/斜度/角度适合编码类别或有序的
# # - shape适合编码类别数据
# # - texture适合编码类别数据

# # 四、色彩策略升级
# # - 主色调：基于隐喻物体的自然色彩
# # - 辅助色：互补色或类似色创造和谐
# # - 强调色：用于数据高亮（可以是红色、橙色等暖色）

# # 五、构图原则
# # - 黄金分割或三分法则布局
# # - 创造视觉焦点和阅读路径
# # - 留白但不空洞，可加入轻微的纹理或图案
# # - 深度通过大小、重叠、透明度表现

# # 六、细节与装饰
# # - 适度的装饰元素增强理解
# # - 小图标或符号辅助说明
# # - 注释可以优雅地融入设计，需要指明数据编码的方式

# # 七、风格关键词（更新版）
# # - Editorial illustration
# # - Infographic design
# # - Data storytelling
# # - Modern vintage aesthetic
# # - Sophisticated minimalism (而非极简主义)
# # - Narrative visualization
# # - Organic data forms
# # - Illustrative statistics

# # 八、具体执行建议
# # - 如果keyword是"tree"：展示真实的树，用树枝粗细、叶子密度编码数据
# # - 如果是"ocean"：画出波浪，波峰高度和频率表示数据变化
# # - 如果是"mountain"：山峰轮廓线，高度直接对应数值

# # 九、避免
# # - 过度抽象的纯几何形状
# # - 不明确的映射关系（必须清晰说明哪个通道编码哪个数据）
# # - 生硬的网格和直线（除非数据本身需要）
# # - 单调的原色块
# # - 缺乏故事性的纯数据展示

# # """

# #     prompt0 = f"""
# # You are creating a text-to-image prompt for a data visualization that uses "{keyword}" as a visual metaphor.

# # {mapping_instructions}

# # **Context:**
# # - Metaphor: {keyword}
# # - Data Fact: {data_fact}
# # - Context Description: {context_description}

# # **Your Task:**
# # Generate a complete, detailed text-to-image prompt (in English) that:

# # 1. **Describes the metaphor structure**: What does {keyword} look like visually?

# # 2. **EXPLICITLY states the data encoding** (THIS IS CRITICAL):
# #    - "The [subitem1]'s [channel1] encodes [field1] data, where [specific mapping description]"
# #    - "The [subitem2]'s [channel2] encodes [field2] data, where [specific mapping description]"
# #    - Be SPECIFIC about how each data value maps to visual attributes

# # 3. **Describes the visual style**: Modern editorial illustration style, sophisticated color palette

# # 4. **Describes composition**: Layout, focus points, use of space

# # **Example of GOOD data encoding description:**
# # "The mosaic tiles' colors encode movie Type, with each genre (Family, Action, Drama) represented by a distinct hue. The tiles' positions along the horizontal axis encode Year, progressing chronologically from left to right."

# # **Example of BAD data encoding description (DO NOT DO THIS):**
# # "Colors convey interest level" ❌ (What data does color encode? Be specific!)
# # "Patterns illustrate timeline" ❌ (How exactly? Which visual attribute maps to which data?)

# # {fixed_requirements}

# # **Output Format:**
# # Return a single, complete prompt (200-300 words) that can be directly used for image generation.
# # Do NOT include any meta-commentary, section headers, or explanations.
# # Just output the raw prompt text.
# # """

# #     return prompt0.strip()
# # #根据语料库的图生成的方案
# def build_prompt0_v5(input_data: Dict[str, Any]) -> str:
#     """
#     v5改进版：从纯几何转向具象隐喻 + 现代信息图表美学
#     """
    
#     keyword = input_data.get("keyword", "")
#     data_fact = input_data.get("dataFact", "")
#     context_description = input_data.get("contextDescription", "")
#     default_plan = input_data.get("defaultPlan", "")
    
#     # 新的设计原则：强调具象隐喻和视觉叙事
#     fixed_requirements = """
# DESIGN PHILOSOPHY: Modern Information Design with Poetic Visual Metaphors

# 一、核心转变：从抽象到具象
# - 将[metaphor_keyword]转化为可识别的具体物体或场景
# - 保留物体的自然形态，通过其属性编码数据
# - 例如：tree→真实的树形，ocean→可见的波浪形态，river→蜿蜒的河流

# 二、视觉风格参考
# - Modern editorial illustration style (像《纽约时报》《经济学人》的信息图)
# - Flat design with subtle depth (扁平但有层次)
# - Hand-crafted digital aesthetic (数字手绘感)
# - Sophisticated color palettes (不限于原色，可用渐变)

# 三、色彩策略升级
# - 主色调：基于隐喻物体的自然色彩
# - 辅助色：互补色或类似色创造和谐
# - 强调色：用于数据高亮（可以是红色、橙色等暖色）
# - 背景：柔和的中性色（米色、浅灰、淡蓝等）

# 四、构图原则
# - 黄金分割或三分法则布局
# - 创造视觉焦点和阅读路径
# - 留白但不空洞，可加入轻微的纹理或图案
# - 深度通过大小、重叠、透明度表现

# 五、数据编码方式
# - 大小 = 数值大小（最直观）
# - 位置 = 时间或类别
# - 颜色深浅 = 强度或重要性
# - 数量/密度 = 频率或总量
# - 形态变化 = 趋势（生长、流动、扩散）

# 六、细节与装饰
# - 适度的装饰元素增强理解（如蛋糕的糖霜滴落表示淘汰）
# - 小图标或符号辅助说明
# - 轻微的纹理增加质感
# - 注释可以优雅地融入设计

# 七、风格关键词（更新版）
# - Editorial illustration
# - Infographic design
# - Data storytelling
# - Modern vintage aesthetic
# - Sophisticated minimalism (而非极简主义)
# - Narrative visualization
# - Organic data forms
# - Illustrative statistics

# 八、具体执行建议
# - 如果keyword是"tree"：展示真实的树，用树枝粗细、叶子密度编码数据
# - 如果是"ocean"：画出波浪，波峰高度和频率表示数据变化
# - 如果是"mountain"：山峰轮廓线，高度直接对应数值

# 九、避免
# - 过度抽象的纯几何形状
# - 生硬的网格和直线（除非数据本身需要）
# - 单调的原色块
# - 缺乏故事性的纯数据展示
# """

#     prompt0 = f"""
# Create a sophisticated data visualization that tells a story through the metaphor of "{keyword}".

# Style: Modern editorial illustration meets information design. Think of The New York Times 
# infographics, with recognizable objects encoding data rather than abstract shapes.

# Visual approach:
# - Use the actual form of {keyword} as the visualization structure
# - Apply a contemporary color palette that enhances comprehension
# - Balance data clarity with aesthetic appeal
# - Include subtle decorative elements that support the data narrative

# Input Data:
# - Metaphor: {keyword}
# - Data Fact: {data_fact}
# - Context: {context_description}
# - Mapping: {default_plan}

# {fixed_requirements}

# The output should feel like a piece from a high-end magazine or museum exhibition - 
# beautiful enough to frame, clear enough to understand immediately.
# """

#     return prompt0.strip()



# # ==================== 主agent类 ====================
# class DesignAgent:
#     """Agent7：图像提示词生成器
#     功能：将Agent6的映射规范转换为可用于文生图的提示词
#     持两种模式：
#     1. v5模式 (use_v5_mode=True): 使用LLM生成具象隐喻风格
#     2. 模板模式 (use_v5_mode=False): 使用固定5句模板
#     """
#     def __init__(self):
#         self.name = "DesignAgent"
#         # 决定是使用v5实验版本模式还是原有模板模式
#         self.use_v5_mode = os.getenv("AGENT7_USE_V5_MODE", "true").lower() in ("1", "true", "yes")
# # ==================== 模版模式====================
#     def _build_prompt(self, mapping_spec: Dict[str, Any]) -> str:
#         # 把 Agent6 输出原样嵌入，让 LLM 自己按规则查 subitem 名称/geometry/variant、通道等。
#         a6 = json.dumps(mapping_spec, ensure_ascii=False)

#         return f"""
# 你将收到一个来自 Agent6 的 JSON（mapping_spec）。请基于其中的字段生成“固定5句”的英文提示词数组（prompt_lines），以及合并后的 image_prompt。
# 严格要求：
# - 只输出**一个**JSON对象，不要额外文字/Markdown。
# - 使用**固定5句模板**，句式与占位含义如下（保持英文）：
#   S1: "Use {{keyword}} as a visual metaphor to portray {{dataFact}} involving {{R1.dataField}} and {{R2.dataField}}."
#   S2: "Encode {{R1.dataField}} with the {{R1.subitem.name}} ({{R1.subitem.geometry}}{{R1.subitem.variant_clause}}) using {{R1.channels_phrase}}; {{R1.effects_clause}}."
#   S3: "Encode {{R2.dataField}} with the {{R2.subitem.name}} ({{R2.subitem.geometry}}{{R2.subitem.variant_clause}}) using {{R2.channels_phrase}}; {{R2.effects_clause}}."
#   S4: "Keep a minimal composition with generous margins and a neutral background; emphasize clear metaphorical shapes and avoid text or axes."
#   S5: "Flat infographic style with crisp edges and a restrained blue-grey palette; light shading only for legibility."
# - 术语来源：
#   - R1= mapping_spec.defaultPlan[0]，R2= mapping_spec.defaultPlan[1]（保持顺序，不做语义假设）
#   - 对于 Rk：
#     • dataField = mapping_spec.defaultPlan[k].dataField  
#     • subitem：到 mapping_spec.field1/field2 中 dataField 匹配的 block 下的 subitemOptions，用 subitem_id == defaultPlan[k].subitemId 查出 name/geometry/variant；variant 存在则 variant_clause=", band"，否则为空
#     • channels_phrase：将 defaultPlan[k].channels 用以下短语映射并用 " and " 连接：
#         position -> "the position channel along the main axis"
#         size -> "the size channel"
#         lightness -> "the lightness channel"
#         color -> "the color channel"
#         texture -> "the texture channel"
#         orientation -> "the orientation channel"
#         shape -> "the shape channel"
#     • effects_clause：按 (geometry, variant, channel) 选择**固定短语**，多通道用 " and " 连接：
#         (area, band, size) -> "higher values make the band thicker"
#         (area, -, size)    -> "areas expand with larger values"
#         (point, -, size)   -> "points grow larger with higher values"
#         (line, -, orientation) -> "angles indicate trend"
#         (*, -, lightness)  -> "higher values appear lighter"
#         (*, -, color)      -> "values progress along a sequential ramp"
#         (*, -, texture)    -> "denser patterns indicate higher values"
#         (*, -, position)   -> "values move farther along the axis"
#         (*, -, shape)      -> "different categories use distinct shapes"
# - 拼接 image_prompt = prompt_lines 用空格连接。
# - data_fact_caption（中文）：若 mapping_spec.contextDescription 非空，用其简化为一句中文摘要；否则用“{{field1.dataField}}在过去一段时间中表现出{{dataFact}}”。

# 【mapping_spec】
# {a6}

# 【输出JSON的**唯一**格式】
# {{
#   "mapping_id": "<复制 mapping_spec.mapping_id>",
#   "keyword": "<复制 mapping_spec.keyword>",
#   "dataFact": "<复制 mapping_spec.dataFact>",
#   "contextDescription": "<复制 mapping_spec.contextDescription>",
#   "prompt_lines": ["S1","S2","S3","S4","S5"],
#   "image_prompt": "<S1 S2 S3 S4 S5 的拼接>",
#   "data_fact_caption": "<中文一句话>"
# }}
# """.strip()
# # ==================== V5模式 ====================
#     def _run_v5_mode(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#         """v5实验版本模式：使用prompt0 + LLM生成prompt1"""
#         try:
#             # 构建input_data，适配v5的输入格式
#             input_data = {
#                 'keyword': mapping_spec.get('keyword', 'metaphor'),
#                 'dataFact': mapping_spec.get('dataFact', 'trend'),
#                 'contextDescription': mapping_spec.get('contextDescription', ''),
#                 'defaultPlan': mapping_spec.get('defaultPlan', []),
#             }
            
#             # 使用实验版本的prompt0构建器
#             prompt0 = build_prompt0_v5(input_data)
            
#             prompt1_raw = llm_generate(prompt0)
            
#             # 清理prompt1中的<think>标签和其他不需要的内容
#             import re
#             # 移除<think></think>标签
#             prompt1 = re.sub(r'<think>.*?</think>', '', prompt1_raw, flags=re.DOTALL)
#             # 只提取实际的prompt内容
#             # 查找反引号包围的prompt
#             match = re.search(r'`([^`]+)`', prompt1)
#             if match:
#                 prompt1 = match.group(1).strip()
#             else:
#                 # 如果没有反引号，尝试找到最后一段有意义的文本
#                 lines = prompt1.strip().split('\n')
#                 # 找到包含"minimalist"或"mountain"等关键词的段落
#                 for line in reversed(lines):
#                     if any(keyword in line.lower() for keyword in ['minimalist', 'mountain', 'metaphor', 'vector']):
#                         prompt1 = line.strip()
#                         break
#             print("=" * 80)
#             print("✅ Agent7 生成的最终Image Prompt:")
#             print(prompt1)
#             print("=" * 80)
#             if prompt1:
#                 # 包装成工具后端期望的格式
#                 return {
#                     "mapping_id": mapping_spec.get("mapping_id"),
#                     "keyword": mapping_spec.get("keyword"),
#                     "dataFact": mapping_spec.get("dataFact"),
#                     "contextDescription": mapping_spec.get("contextDescription", ""),
#                     "prompt_lines": [prompt1],  # v5模式下prompt1就是完整prompt
#                     "image_prompt": prompt1,
#                     "data_fact_caption": mapping_spec.get("contextDescription") or f"{mapping_spec.get('keyword', '数据')}呈现{mapping_spec.get('dataFact', '趋势')}特征",
#                     "v5_metadata": {
#                         "version": "v5_optimized",
#                         "mode": "enhanced_mapping_clarity",
#                         "encoding_enforced": True
#                     }
#                 }
#             else:
#                 # 如果LLM生成失败，回退到模板模式
#                 return self._run_template_mode(mapping_spec)
                
#         except Exception as e:
#             print(f"v5模式失败，回退到模板模式: {e}")
#             return self._run_template_mode(mapping_spec)

#     def _run_template_mode(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#         prompt = self._build_prompt(mapping_spec)
#         raw = llm_generate(prompt)

#         # 清洗 & 解析
#         if "```" in raw:
#             raw = raw.split("```")[-2] if raw.count("```") >= 2 else raw.replace("```", "")
#         raw = raw.strip()
#         try:
#             return clean_json_response(raw)
#         except Exception as e:
#             # 直接抛出错误，不生成占位数据
#             error_msg = f"DesignAgent failed to parse LLM response: {str(e)}"
#             print(error_msg)
#             print(f"Raw response (first 500 chars): {raw[:500]}")
#             raise ValueError(error_msg)
        
        

#     def run(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#         """主运行函数：根据配置选择v5模式或模板模式"""
#         if self.use_v5_mode:
#             return self._run_v5_mode(mapping_spec)
#         else:
#             return self._run_template_mode(mapping_spec)
#     #  def run(self, mapping_spec: Dict[str, Any]) -> Dict[str, Any]:
#     #     prompt = self._build_prompt(mapping_spec)
#     #     raw = llm_generate(prompt)

#     #     # 解析（仅做最小清洗）
#     #     if "```" in raw:
#     #         raw = raw.split("```")[-2] if raw.count("```") >= 2 else raw.replace("```", "")
#     #     raw = raw.strip()

#     #     try:
#     #         obj = json.loads(raw)
#     #         return obj
#     #     except Exception as e:
#     #         # 解析失败时，抛错便于观察 LLM 返回（保持极简，不写本地拼接规则）
#     #         raise ValueError(f"LLM JSON parse failure: {e}\nRAW:\n{raw}")

# # 版本v1
# # """
# # Agent7: 图像设计提示词生成 Agent（DesignAgent）
# # 作用：将上下文 + 本体 + 喻体 + 映射通道生成图像提示词 + 数据事实
# # """

# # from typing import Dict, Any
# # import os
# # import json
# # from langchain_openai import ChatOpenAI
# # from langchain.schema import HumanMessage, SystemMessage

# # def llm_generate(prompt: str) -> str:
# #     chat = ChatOpenAI(
# #         model="gpt-4",
# #         temperature=0.4,
# #         openai_api_key=os.getenv("OPENAI_API_KEY"),
# #         openai_api_base=os.getenv("OPENAI_API_BASE", "https://ai-yyds.com/v1"),
# #     )

# #     messages = [
# #         SystemMessage(content="你是一个数据可视化设计专家，擅长构建面向图像生成模型的提示词与描述。"),
# #         HumanMessage(content=prompt)
# #     ]

# #     response = chat(messages)
# #     return response.content.strip()

# # class DesignAgent:
# #     def __init__(self):
# #         self.name = "DesignAgent"
    
# #     def run(self,
# #             source: str,
# #             target: str,
# #             mapping: list,
# #             data_fact: str,
# #             style_context: str = "极简主义图表风格") -> Dict[str, Any]:
# #         """
# #         生成图像提示词和数据事实描述
        
# #         Args:
# #             source: 本体（数据字段）
# #             target: 喻体关键词
# #             mapping: 映射通道列表
# #             data_fact: 数据特征
# #             style_context: 图像风格上下文
            
# #         Returns:
# #             Dict包含图像提示词和数据事实描述
# #         """
# #         # TODO: 实现Agent逻辑
# #         # 1. 融合本体、喻体、映射关系和上下文信息
# #         # 2. 生成适用于稳定扩散模型的图像提示词
# #         # 3. 生成数据事实描述文本
# #         # 4. 支持多语言提示或图表类型标签
# #         prompt = self._build_design_prompt(source, target, mapping, data_fact, style_context)
# #         response = llm_generate(prompt)

# #         if "```" in response:
# #             response = response.split("```")[1].strip()  # 提取 ``` 中间内容

# #         try:
# #             result = json.loads(response)
# #         except Exception as e:
# #             print("⚠️ LLM返回解析失败:", e)
# #             print("原始内容:", response)
# #             result = {
# #                 "image_prompt": f"A minimalist chart using {target} as a metaphor for {source}, visualized through {', '.join(mapping)}.",
# #                 "data_fact_caption": f"{source} exhibits a trend of {data_fact} over time."
# #             }
# #         return result
# #         # 临时返回示例数据
# #         return {
# #             "image_prompt": f"一幅{style_context}的图像，以{target}隐喻{source}。通过{', '.join(mapping)}表现数据的{data_fact}趋势。",
# #             "data_fact_caption": f"{source}在过去一段时间中持续{data_fact}"
# #         }
    
# #     def _build_design_prompt(self, source: str, target: str, mapping: list, data_fact: str, style_context: str) -> str:
# #         """
# #         构建设计提示词
# #         """
# #         mapping_str = "、".join(mapping)
# #         prompt = f"""
# # 请根据以下信息生成稳定扩散模型的图像生成提示词：

# # 本体：{source}
# # 喻体：{target}
# # 映射通道：{mapping_str}
# # 数据特征：{data_fact}
# # 图像风格：{style_context}

# # 要求：
# # 1. 生成包含视觉引导的中英文提示词
# # 2. 简要的数据描述句，用于支持模型图像生成与解释
# # 3. 确保提示词具有明确的视觉表现力
# # 4. 数据事实描述应该简洁明了

# # 请返回JSON格式：
# # {{
# #     "image_prompt": "图像生成提示词",
# #     "data_fact_caption": "数据事实描述"
# # }}
# # 请不要输出 markdown 代码块或注释，只返回纯JSON
# # """
# #         return prompt 



# # #融入蒙德里安配色 + Josef Müller-Brockmann 
# # def build_prompt0_v5(input_data: Dict[str, Any]) -> str:
# #     """
# #     v5改进版：融入蒙德里安配色 + Josef Müller-Brockmann
# #     """
    
# #     keyword = input_data.get("keyword", "")
# #     data_fact = input_data.get("dataFact", "")
# #     context_description = input_data.get("contextDescription", "")
# #     default_plan = input_data.get("defaultPlan", "")
    
# #     # 修改点1：替换原有的fixed_requirements（第73-115行）
# #     fixed_requirements = """
# # 本版融合蒙德里安色彩系统，强调Josef Müller-Brockmann风格的数据表达。

# # 一、设计语言
# # - 风格基础：Josef Müller-Brockmann的瑞士平面设计 + 极简主义
# # - 色彩系统：蒙德里安三原色（纯红#FF0000、纯蓝#0000FF、纯黄#FFFF00）+ 黑色结构线 + 白色负空间
# # - 构成原则：理性的网格系统、数学化的比例关系、功能主导形式

# # 二、视觉执行
# # - 使用[metaphor_vehicle]作为几何化结构来编码[data_tenor]
# # - 通过蒙德里安色块大小、位置、密度表达数据关系
# # - Josef Müller-Brockmann的网格系统确保信息层级清晰

# # 三、色彩映射
# # - 红色块：最高值或最重要数据
# # - 蓝色块：中等值或支撑性数据  
# # - 黄色块：低值或细节数据
# # - 黑色线条：分隔不同数据维度，线宽表示层级
# # - 白色空间：基准值或数据间的关系

# # 五、映射清晰度
# # - 一对一：一种数据维度对应一种视觉属性
# # - 色块大小 = 数值大小
# # - 色块位置 = 时间或类别维度
# # - 色块颜色（红/蓝/黄）= 数据重要性层级

# # 六、风格锚点（修改点2：新增的风格描述）
# # - Josef Müller-Brockmann poster design 
# # - Mondrian neoplasticism color blocks
# # - Swiss International Style grid
# # - De Stijl movement aesthetics
# # - Minimalist data visualization
# # - Clean vector graphics
# # - Mathematical precision
# # - Functional beauty

# # 七、禁忌
# # - 禁止渐变、阴影、3D效果
# # - 禁止装饰性元素
# # - 禁止曲线或有机形状
# # - 禁止超出红蓝黄黑白的色彩
# # - 禁止模糊边缘或纹理

# # 八、输出要求
# # - 产出具有美术馆品质的数据艺术作品
# # - 保持蒙德里安的纯粹
# # - 体现Josef Müller-Brockmann的信息设计精准度
# # - 完成度提升至85%（非草图），呈现完整的视觉作品
# # """

# #     # 修改点3：更新prompt0的组装部分
# #     prompt0 = f"""
# # Create a data visualization in the style of Josef Müller-Brockmann's Swiss design, 
# # using Mondrian's color system.

# # Input Data:
# # - Keyword (metaphor): {keyword}
# # - Data Fact: {data_fact}
# # - Context: {context_description}
# # - Mapping Plan: {default_plan}

# # {fixed_requirements}

# # Task: Generate a detailed image generation prompt that creates a sophisticated data artwork combining:
# # 1. Mondrian's primary color blocks (red, blue, yellow, black lines, white space)
# # 2. Josef Müller-Brockmann's mathematical grid system
# # 4. Clear data-to-visual mappings through color, size, and position

# # The output should be gallery-quality, immediately recognizable as modernist design, 
# # while effectively encoding the data relationships.
# # """

# #     return prompt0.strip()

# # #融入蒙德里安配色 + Josef Müller-Brockmann + 包豪斯风格
# # def build_prompt0_v5(input_data: Dict[str, Any]) -> str:
# #     """
# #     v5改进版：融入蒙德里安配色 + Josef Müller-Brockmann + 包豪斯风格
# #     """
    
# #     keyword = input_data.get("keyword", "")
# #     data_fact = input_data.get("dataFact", "")
# #     context_description = input_data.get("contextDescription", "")
# #     default_plan = input_data.get("defaultPlan", "")
    
# #     # 修改点1：替换原有的fixed_requirements（第73-115行）
# #     fixed_requirements = """
# # 本版融合包豪斯理性美学与蒙德里安色彩系统，强调几何构成的数据表达。

# # 一、设计语言
# # - 风格基础：Josef Müller-Brockmann的瑞士平面设计 + 包豪斯几何构成 + 极简主义
# # - 色彩系统：蒙德里安三原色（纯红#FF0000、纯蓝#0000FF、纯黄#FFFF00）+ 黑色结构线 + 白色负空间
# # - 构成原则：理性的网格系统、数学化的比例关系、功能主导形式

# # 二、视觉执行
# # - 使用[metaphor_vehicle]作为几何化结构来编码[data_tenor]
# # - 通过蒙德里安色块大小、位置、密度表达数据关系
# # - Josef Müller-Brockmann的网格系统确保信息层级清晰
# # - 包豪斯的"形式追随功能"原则指导设计决策

# # 三、色彩映射
# # - 红色块：最高值或最重要数据
# # - 蓝色块：中等值或支撑性数据  
# # - 黄色块：低值或细节数据
# # - 黑色线条：分隔不同数据维度，线宽表示层级
# # - 白色空间：基准值或数据间的关系

# # 四、几何构成规则
# # - 所有元素基于矩形、正方形、直线构成
# # - 严格的直角关系，无斜线或曲线
# # - 黄金分割或模数化的比例系统
# # - 不对称平衡创造视觉张力

# # 五、映射清晰度
# # - 一对一：一种数据维度对应一种视觉属性
# # - 色块大小 = 数值大小
# # - 色块位置 = 时间或类别维度
# # - 色块颜色（红/蓝/黄）= 数据重要性层级

# # 六、风格锚点（修改点2：新增的风格描述）
# # - Josef Müller-Brockmann poster design
# # - Bauhaus geometric composition  
# # - Mondrian neoplasticism color blocks
# # - Swiss International Style grid
# # - De Stijl movement aesthetics
# # - Minimalist data visualization
# # - Clean vector graphics
# # - Mathematical precision
# # - Functional beauty

# # 七、禁忌
# # - 禁止渐变、阴影、3D效果
# # - 禁止装饰性元素
# # - 禁止曲线或有机形状
# # - 禁止超出红蓝黄黑白的色彩
# # - 禁止模糊边缘或纹理

# # 八、输出要求
# # - 产出具有美术馆品质的数据艺术作品
# # - 保持包豪斯的理性与蒙德里安的纯粹
# # - 体现Josef Müller-Brockmann的信息设计精准度
# # - 完成度提升至85%（非草图），呈现完整的视觉作品
# # """

# #     # 修改点3：更新prompt0的组装部分
# #     prompt0 = f"""
# # Create a data visualization in the style of Josef Müller-Brockmann's Swiss design, 
# # using Mondrian's color system and Bauhaus geometric principles.

# # Input Data:
# # - Keyword (metaphor): {keyword}
# # - Data Fact: {data_fact}
# # - Context: {context_description}
# # - Mapping Plan: {default_plan}

# # {fixed_requirements}

# # Task: Generate a detailed image generation prompt that creates a sophisticated data artwork combining:
# # 1. Mondrian's primary color blocks (red, blue, yellow, black lines, white space)
# # 2. Josef Müller-Brockmann's mathematical grid system
# # 3. Bauhaus principles of geometric composition and functional minimalism
# # 4. Clear data-to-visual mappings through color, size, and position

# # The output should be gallery-quality, immediately recognizable as modernist design, 
# # while effectively encoding the data relationships.
# # """

# #     return prompt0.strip()

# # 原先线稿风格
# # def build_prompt0_v5(input_data: Dict[str, Any]) -> str:
# #     """
# #     完全按照实验版本的v5_prompt0_builder.py构建prompt0
    
# #     v5原则强调：
# #     - 隐喻为结构，数据表达趋势即可，装饰最少
# #     - 输出概念性视觉线稿（约30%完成度）
# #     - 给设计师保留70%的延展空间
# #     - 去数值、保关系，突出变量间的相对关系与趋势
# #     - 无坐标轴设计，以隐喻结构承载信息
# #     """
    
# #     keyword = input_data.get("keyword", "")
# #     data_fact = input_data.get("dataFact", "")
# #     context_description = input_data.get("contextDescription", "")
# #     default_plan = input_data.get("defaultPlan", "")
    
# #     # 这里是从实验版本完整搬过来的中文原则
# #     fixed_requirements = """
# # 本版强调"隐喻为结构，数据表达趋势即可，装饰最少"。输出定位为概念性视觉线稿（约30%完成度），给设计师保留70%的延展空间。

# # 一、目标与完成度
# # - 使用[metaphor_vehicle]作为整体结构来编码[data_tenor]；传达趋势（而非精确数值）
# # - 产出概念草图（约30%完成度）：保留清晰的隐喻结构与数据映射关系，不追求像素级细节
# # - 去数值、保关系：避免具体数值渲染，突出变量间的相对关系与趋势
# # - 无坐标轴设计（negative: no axes, no ticks, no gridlines）

# # 二、设计优先级与权重
# # - 优先级：隐喻载体 > 数据映射 >> 装饰细节
# # - 视觉权重建议：隐喻结构承载信息，避免装饰性元素

# # 三、信息维度与留白
# # - 视觉映射通道严格根据输入数据来确定，不要自己创造通道
# # - 移除装饰性背景纹理，保留充足留白以增强可读性与层次感
# # - 无坐标轴布局：以隐喻结构承载信息；禁止：no axes, no ticks, no gridlines；如需对齐，仅允许极淡的对齐点/极短虚线（不得形成网格或坐标感）

# # 四、映射规则与可读性
# # - 一对一：一种数据维度对应一种视觉通道，避免复用与歧义
# # - 明示映射：以自然语言注释的方式写清"数据字段 → 视觉通道"，并嵌入隐喻主体
# # - 空间逻辑：时间/顺序优先用位置通道编码，强化阅读路径
# # - 映射需写作注释并直接嵌入隐喻主体，不得以坐标轴/刻度形式表现

# # 五、版式与层次
# # - 建立前景/中景/背景的清晰结构，避免要素堆叠与相互遮挡
# # - 使用矢量几何元素，构图极简、边缘清晰

# # 六、色彩与文字
# # - 文字最小化：避免大段文本与密集标签，仅保留必要注释
# # - 背景用纯白色

# # 七、隐喻即结构（弱化坐标轴）
# # - 不描述"像图表/像可视化"，而是"使用某隐喻作为整体结构编码数据"
# # - 优先用自然布局替代坐标轴，例如：
# #   - arranged as concentric rings like tree rings
# #   - displayed as a flowing hourglass shape
# #   - scattered across a field of poppies

# # 八、禁忌与反例
# # - 禁止层层堆叠导致对应关系不清
# # - 禁止与数据无关的装饰元素、纹理、复杂背景
# # - 禁止写实风格与摄影质感
# # - 禁止信息图（主体附近有过多冗余解释）

# # 九、数据事实融入
# # - 依据数据事实选用可控的动态词：rising / shrinking / oscillating / steady / spiking 等
# # - 只需要能反应大致趋势即可

# # 十、风格锚点
# # - 使用一致的风格锚点以稳态输出：clean vector graphics, abstract minimalism, sketch，balanced composition, subtle metaphorical elegance

# # 十一、视觉通道示例化表达
# # - each flower represents one victim, petal color = category, size = age
# # - each ring in the tree cross-section = one decade, thickness = population growth
# # """

# #     # 组装完整的prompt0，完全按实验版本的格式
# #     prompt0 = f"""
# # Input Data:
# # - Keyword: {keyword}
# # - Data Fact: {data_fact}
# # - Context Description: {context_description}
# # - Default Plan: {default_plan}

# # {fixed_requirements}

# # Task: Generate a detailed prompt1 for text-to-image generation that follows these principles exactly.
# # """

# #     return prompt0.strip()