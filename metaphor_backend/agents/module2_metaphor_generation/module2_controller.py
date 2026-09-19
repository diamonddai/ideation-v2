"""
模块二：隐喻生成模块控制器
处理前端选择的 boundField 进行发散
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import asyncio
import aiohttp
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# 导入各个 Agent
from .variation_planner_agent import variation_planner_agent, VariationPlannerInput, BoundField as VPBoundField
from .feature_rewrite_agent import feature_rewrite_agent, FeatureRewriteInput, MetaphorVariation as FRMetaphorVariation

# 导入缓存工具
from utils.cache_utils import cache

router = APIRouter()

class BoundField(BaseModel):
    field: str
    dataFact: str

class MetaphorGenerationInput(BaseModel):
    boundField: VPBoundField
    blindRatio: float = 0.4
    totalLimit: int = 30

class ThemeInfo(BaseModel):
    name: str
    color: str

class LinkInfo(BaseModel):
    source: str
    target: str
    distance: float

class EnhancedVariation(BaseModel):
    id: str
    field: str
    keyword: str
    dataFact: str
    theme: str
    method: str  # "guided" or "blind"
    guidedmethod: Optional[str] = None  # 只有guided模式有值
    guided2ndLevelMethod: Optional[str] = None  # 只有guided模式有值
    rNorm: float
    thumb: str
    mapping_spec: Optional[dict] = None  # ✅ 添加这个字段
    dimensions: Optional[List[str]] = None  # ✅ 添加dimensions字段

class MetaphorGenerationOutput(BaseModel):
    variations: List[EnhancedVariation]
    links: List[LinkInfo]
    themes: List[ThemeInfo]
    message: str

# 辅助函数
def get_theme_classification_prompt(keyword: str) -> str:
    """生成主题分类提示词"""
    return f"""
你是一个主题分类专家。请将英文名词"{keyword}"分类到以下5个主题之一：

1. Nature(自然物体)：指自然界中存在的、未经人类改造的事物。
   例如：海洋、岩石、土壤、太阳、山脉、河流、森林、云朵、种子、花朵、树木、波浪、风暴
   注意：种子、花朵、树木等植物相关词汇属于Nature，不是Life；波浪、风暴等自然现象也属于Nature

2. Artifact(人工制品)：指具人造属性、用途清晰的物体。
   例如：桌子、椅子、书籍、瓶子、电视、汽车、电脑、建筑、工具、桥梁

3. Body(身体部位)：指身体的各个部分，描述的是身体的一部分或器官。
   例如：人脸、鼻子、手臂、眼睛、心脏、大脑、手指、手、脚

4. Life(生命体)：指有生命的生物体，通常是动物。
   例如：蚂蚁、狗、猫、鸟、鱼、人类、动物
   注意：植物相关词汇(种子、花朵、树木)属于Nature，不是Life

5. Others(其他)：无法归类为上述任何一类的抽象概念、现象、状态等。
   例如：阴影、脚本、剧本、经验、连接、潜力、记忆、梦想、旅程、故事、传说、场景、情节
   注意：抽象概念、现象、状态等通常属于Others；故事、传说、场景等抽象概念属于Others，不是Life

请只返回主题名称(Nature/Artifact/Body/Life/Others)，不要其他内容。
"""

async def classify_theme(keyword: str) -> str:
    """对keyword进行主题分类"""
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
        )
        
        prompt = get_theme_classification_prompt(keyword)
        messages = [
            SystemMessage(content="你是主题分类专家，请根据用户提示进行准确分类。"),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        theme = response.content.strip()
        
        # 验证返回的主题是否有效
        valid_themes = ["Nature", "Artifact", "Body", "Life", "Others"]
        if theme in valid_themes:
            return theme
        else:
            return "Others"  # 默认分类
            
    except Exception as e:
        print(f"主题分类失败: {e}")
        return "Others"

async def classify_themes_batch(keywords: List[str]) -> Dict[str, str]:
    """
    批量分类所有keywords的主题(一次LLM调用完成所有分类)
    性能提升：30个变体从30次调用降为1次调用
    """
    if not keywords:
        return {}
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
        )
        
        keywords_str = ", ".join([f'"{kw}"' for kw in keywords])
        
        prompt = f"""
你是一个主题分类专家。请将待分类词汇"{keywords_str}"中的每个词汇分类到以下5个主题之一：
**待分类词汇：**
{keywords_list}
**分类规则：**

**Nature(自然物体)** - 自然界存在的事物，包括植物、自然现象
 包括：ocean, river, mountain, forest, cloud, storm, rain, wind, wave, thunder
 包括：sun, moon, star, light, shadow(自然光影)
 包括：tree, flower, seed, plant, root, leaf(植物),tree rings
 包括：rock, soil, sand, water, fire
 不包括：animal动物(属于Life)

**Artifact(人工制品)** - 人类制造的具体物品
 包括：table, chair, book, car, building, bridge, tool, machine, computer, ring
 不包括：抽象概念

**Body(身体部位)** - 身体的组成部分
包括：face, eye, hand, heart, brain, finger, arm, leg,nose,lip,mouth
不包括：完整的人或动物(属于Life)

**Life(生命体)** - 有生命的动物
包括：ant, dog, cat, bird, fish, human, animal
不包括：植物(属于Nature)

**Others(其他)** - 用于抽象概念、情感、关系
包括：memory, dream, story, journey, connection, experience, potential, struggle
不包括：(cloud/storm/plant/plant)属于Nature,不是Others

**关键提醒：**
- cloud, storm, rain, wind 等自然现象 → Nature(不是Others)
- tree, flower, plant, seed 等植物 → Nature(不是Life)


主题名只限于这五个(Nature/Artifact/Body/Life/Others)，不要有其他命名。

请返回JSON格式：
{{
  "keyword1": "主题名",
  "keyword2": "主题名",
  ...
}}

只返回JSON，不要其他内容。
"""
        
        messages = [
            SystemMessage(content="你是主题分类专家，返回有效的JSON。"),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        result_text = response.content.strip()
        
        # 清理markdown标记
        result_text = re.sub(r'```json\s*', '', result_text)
        result_text = re.sub(r'```\s*', '', result_text)
        result_text = result_text.strip()
        
        classifications = json.loads(result_text)
        
        # 验证并填充默认值
        valid_themes = ["Nature", "Artifact", "Body", "Life", "Others"]
        result = {}
        for kw in keywords:
            theme = classifications.get(kw, "Others")
            result[kw] = theme if theme in valid_themes else "Others"
        
        print(f"✅ 批量分类完成：{len(result)}个关键词")
        return result
            
    except Exception as e:
        print(f"⚠️ 批量主题分类失败: {e}，使用默认值")
        return {kw: "Others" for kw in keywords}

def calculate_semantic_distance(keyword1: str, keyword2: str) -> float:
    """计算两个关键词之间的语义距离(简化版本，使用字符串相似度)"""
    # 这里使用简化的字符串相似度，实际项目中应该使用词向量模型
    # 如 Word2Vec, FastText, 或 BERT 等
    
    # 简单的编辑距离归一化
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    max_len = max(len(keyword1), len(keyword2))
    if max_len == 0:
        return 0.0
    
    distance = levenshtein_distance(keyword1.lower(), keyword2.lower())
    normalized_distance = distance / max_len
    
    # 转换为相似度(0-100)，距离越小相似度越高
    similarity = (1 - normalized_distance) * 100
    return round(similarity, 1)

def normalize_distances(distances: List[float]) -> List[float]:
    """归一化距离列表到0-1范围"""
    if not distances:
        return []
    
    min_dist = min(distances)
    max_dist = max(distances)
    
    if max_dist == min_dist:
        return [0.5] * len(distances)  # 如果所有距离相同，返回0.5
    
    normalized = [(d - min_dist) / (max_dist - min_dist) for d in distances]
    return [round(n, 2) for n in normalized]

def get_guided_method_mapping(dimension: str) -> tuple:
    """根据维度返回guidedMethod和guided2ndLevelMethod"""
    mapping = {
        # 语义维度
        "因果关系": ("语义维度", "因果关系"),
        "类属关系": ("语义维度", "类属关系"), 
        "象征关系": ("语义维度", "象征关系"),
        
        # 功能维度
        "行为": ("功能维度", "行为"),
        "用途": ("功能维度", "用途"),
        
        # 感知维度
        "颜色": ("感知维度", "颜色"),
        "形状": ("感知维度", "形状"),
        "尺寸": ("感知维度", "尺寸"),
        
        # 结构维度
        "空间": ("结构维度", "空间"),
        "时间": ("结构维度", "时间")
    }
    
    return mapping.get(dimension, (None, None))

def generate_thumb_url(keyword: str) -> str:
    """生成假图片地址"""
    return f"https://ex.com/thumbs/{keyword.lower()}.png"

async def balance_themes(enhanced_variations: List[EnhancedVariation],
                         original_keyword: str,
                         context_description: str,
                         total_limit: int) -> List[EnhancedVariation]:
    """
    主题均衡后处理：确保每个主题至少有指定数量的结果
    """
    ENABLE_THEME_BALANCE = os.getenv("ENABLE_THEME_BALANCE", "true").lower() in ["1", "true", "yes"]
    
    if not ENABLE_THEME_BALANCE:
        return enhanced_variations

    # 使用 totalLimit / 5 作为每个主题的最小数量
    MIN_PER_THEME = max(1, total_limit // 5)
    # 计算理想分布：每个主题应该有多少个
    IDEAL_PER_THEME = total_limit // 5
    MAX_PER_THEME = IDEAL_PER_THEME + 1  # 允许每个主题最多比理想数量多1个

    # 统计现有分布
    theme_counts = {}
    for v in enhanced_variations:
        theme_counts[v.theme] = theme_counts.get(v.theme, 0) + 1

    print(f"🎯 主题分布统计: {theme_counts}")
    print(f"🎯 每主题最小数量: {MIN_PER_THEME}, 理想数量: {IDEAL_PER_THEME}, 最大数量: {MAX_PER_THEME}")

    target_themes = ["Nature", "Artifact", "Body", "Life", "Others"]
    
    # 检查是否需要均衡：如果有主题数量超过最大数量，或者有主题数量少于最小数量
    need_balance = False
    for theme in target_themes:
        count = theme_counts.get(theme, 0)
        if count < MIN_PER_THEME or count > MAX_PER_THEME:
            need_balance = True
            break
    
    if not need_balance:
        print("🎯 主题分布已均衡，跳过主题均衡")
        return enhanced_variations
    
    # 计算需要补齐的主题
    need_fill = [(t, max(0, MIN_PER_THEME - theme_counts.get(t, 0))) for t in target_themes]
    print(f"🎯 需要补齐的主题: {need_fill}")

    print(f"🎯 主题均衡：需要补齐 {sum(n for _, n in need_fill)} 个结果(每主题至少 {MIN_PER_THEME} 个)")

    # 只使用 LLM 生成补齐，不使用"借位"补齐
    filled = list(enhanced_variations)
    next_idx = len(filled) + 1
    def new_id(i): return f"m{(i):02d}"

    # 使用 LLM 生成同主题导向候选
    try:
        llm = ChatOpenAI(
            model=os.getenv("BALANCE_THEME_LLM_MODEL", "gpt-4o-mini"),
            temperature=0.5,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
        )
        
        for theme, deficit in need_fill:
            if deficit <= 0:
                continue
                
            print(f"🎯 为主题 '{theme}' 生成 {deficit} 个变体...")
                
            sys_prompt = (
                "你是名词生成助手。给出若干英文普通名词，适合归类到给定主题(Nature/Artifact/Body/Life/Others)，"
                "避免专有名词、复数、动词/形容词、与输入 field 形态相同，仅返回 JSON 数组。"
            )
            user_prompt = f"""field: {original_keyword}
context: {context_description}
target_theme: {theme}
need: {deficit}
"""
            resp = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
            import json, re
            text = (resp.content or "").strip()
            print(f"🎯 LLM 响应: {text[:100]}...")
            words = []
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    words = [w for w in parsed if isinstance(w, str)]
            except Exception:
                words = re.findall(r"[A-Za-z][a-z]{2,}", text)
            
            # 过滤技术术语
            def is_technical_term(keyword: str) -> bool:
                """检查是否为技术术语或文件后缀"""
                keyword_lower = keyword.lower()
                
                # 文件后缀
                file_extensions = {
                    'json', 'xml', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c', 'h',
                    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                    'jpg', 'jpeg', 'png', 'gif', 'svg', 'mp4', 'avi', 'mp3', 'wav',
                    'zip', 'rar', 'tar', 'gz', 'exe', 'dll', 'so', 'dylib'
                }
                
                if keyword_lower in file_extensions:
                    return True
                
                # 技术术语
                tech_terms = {
                    'api', 'url', 'http', 'https', 'sql', 'mysql', 'redis', 'mongodb',
                    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'rest', 'graphql',
                    'oauth', 'jwt', 'ssl', 'tls', 'cors', 'csrf', 'xss', 'csrf',
                    'json', 'yaml', 'xml', 'csv', 'tsv', 'log', 'config', 'env',
                    'git', 'github', 'gitlab', 'bitbucket', 'npm', 'yarn', 'pip',
                    'node', 'react', 'vue', 'angular', 'django', 'flask', 'spring'
                }
                
                if keyword_lower in tech_terms:
                    return True
                
                return False
            
            filtered_words = []
            for w in words:
                if not is_technical_term(w.lower()):
                    filtered_words.append(w)
                else:
                    print(f"🎯 过滤技术术语: '{w}'")
            
            words = filtered_words
            print(f"🎯 解析出的词汇: {words}")
                
            for w in words[:deficit]:
                dup = EnhancedVariation(
                    id=new_id(next_idx),
                    field=original_keyword,
                    keyword=w.lower(),
                    dataFact=filled[0].dataFact if filled else "",
                    theme=theme,
                    method="blind",
                    guidedmethod=None,
                    guided2ndLevelMethod=None,
                    rNorm=0.0,
                    thumb=generate_thumb_url(w),
                    mapping_spec=None,
                    dimensions=filled[0].dimensions if filled and filled[0].dimensions else []
                )
                filled.append(dup)
                next_idx += 1
                
        print(f"🔁 主题均衡：LLM 兜底生成完成")
    except Exception as e:
        print(f"⚠️ 主题均衡：LLM 兜底失败: {e}")

    # 注意：不在这里截断，让调用方处理数量限制
    print(f"✅ 主题均衡完成：{len(filled)} 个结果")
    return filled

async def generate_real_image(field: str, keyword: str, data_fact: str, context_description: str) -> str:
    """
    调用模块三生成真实图片
    - 3分钟超时机制
    - 失败时返回假URL
    """
    try:
        # 准备模块三的请求数据
        module3_data = {
            "field": field,
            "keyword": keyword,
            "data_fact": data_fact,
            "method": 1,  # GUIDED模式
            "context_description": context_description
        }
        
        # 设置3分钟超时
        timeout = aiohttp.ClientTimeout(total=180)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = "http://localhost:8000/api/v1/module3/generate-visualization"
            
            print(f"🖼️ 正在为 '{keyword}' 生成图片...")
            
            async with session.post(url, json=module3_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") and result.get("image_url"):
                        image_url = result["image_url"]
                        print(f"✅ '{keyword}' 图片生成成功: {image_url}")
                        return image_url
                    else:
                        print(f"⚠️ '{keyword}' 图片生成失败: {result.get('error', '未知错误')}")
                        return generate_thumb_url(keyword)
                else:
                    print(f"❌ '{keyword}' 模块三调用失败: HTTP {response.status}")
                    return generate_thumb_url(keyword)
                    
    except asyncio.TimeoutError:
        print(f"⏰ '{keyword}' 图片生成超时(3分钟)")
        return generate_thumb_url(keyword)
    except Exception as e:
        print(f"❌ '{keyword}' 图片生成异常: {str(e)}")
        return generate_thumb_url(keyword)





@router.post("/generate-metaphors", response_model=MetaphorGenerationOutput)
async def generate_metaphors(input_data: MetaphorGenerationInput):
    """
    生成隐喻变体(优化版本)
    优化点：
    1. 自动调整并发数
    2. 分批处理大量变体
    3. 更长的超时时间
    """
    try:
        # 1. 从缓存获取 contextDescription
        context_description = cache.get("contextDescription")
        all_bound_fields = cache.get("boundFields") or []
        
        # 找到当前选中的boundField
        current_dimensions = []
        for bf in all_bound_fields:
            if bf.get("field") == input_data.boundField.field:
                current_dimensions = bf.get("dimensions", [])
                break
        
        print(f"📊 当前Subject的dimensions: {current_dimensions}")
        
        # 2. 调用 Agent4：隐喻发散
        print("🎯 调用 Agent4：隐喻发散...")
        agent4_input = VariationPlannerInput(
            boundField=input_data.boundField,
            contextDescription=context_description,
            blindRatio=input_data.blindRatio,
            totalLimit=input_data.totalLimit,
        )
        agent4_result = await variation_planner_agent(agent4_input)
        print(f"[Controller] Agent4 返回 {len(agent4_result.variations)} 个变体")
        
        # 3. 调用 Agent5：数据事实融合改写
        print("✏️ 调用 Agent5：数据事实融合改写...")
        fr_variations = [
            FRMetaphorVariation(**v.model_dump()) for v in agent4_result.variations
        ]
        agent5_input = FeatureRewriteInput(variations=fr_variations)
        agent5_result = await feature_rewrite_agent(agent5_input)
        
        # 4. 主题分类前去重和限制数量
        print("🎨 进行主题分类前去重...")
        seen_keywords = set()
        unique_enhanced_variations = []
        for var in agent5_result.enhancedVariations:
            if var.keyword not in seen_keywords:
                seen_keywords.add(var.keyword)
                unique_enhanced_variations.append(var)
            else:
                print(f"[Controller] 去重：移除重复关键词 '{var.keyword}'")
        
        print(f"[Controller] Agent5 返回 {len(agent5_result.enhancedVariations)} 个变体，去重后 {len(unique_enhanced_variations)} 个")
        
        # 严格限制数量
        if len(unique_enhanced_variations) > input_data.totalLimit:
            print(f"[Controller] 严格截断：从 {len(unique_enhanced_variations)} 个变体截断到 {input_data.totalLimit} 个")
            unique_enhanced_variations = unique_enhanced_variations[:input_data.totalLimit]
        # 5. 批量主题分类(性能优化：一次LLM调用完成所有分类)
        print("🎨 批量主题分类...")
        all_keywords = [var.keyword for var in unique_enhanced_variations]
        theme_map = await classify_themes_batch(all_keywords)
        
        enhanced_variations = []
        for i, var in enumerate(unique_enhanced_variations):
            theme = theme_map.get(var.keyword, "Others")
            
            guided_method = None
            guided_2nd_level_method = None
            
            if var.method == 1:  # GUIDED模式
                original_var = agent4_result.variations[i] if i < len(agent4_result.variations) else None
                if original_var and hasattr(original_var, 'dimensions') and original_var.dimensions:
                    dimension_index = i % len(original_var.dimensions)
                    dimension = original_var.dimensions[dimension_index]
                    guided_method, guided_2nd_level_method = get_guided_method_mapping(dimension)
            
            enhanced_var = EnhancedVariation(
                id=f"m{i+1:02d}",
                field=var.field,
                keyword=var.keyword,
                dataFact=var.dataFact,
                theme=theme,
                method="guided" if var.method == 1 else "blind",
                guidedmethod=guided_method,
                guided2ndLevelMethod=guided_2nd_level_method,
                rNorm=0.0,
                thumb=generate_thumb_url(var.keyword),
                mapping_spec=None,
                dimensions=current_dimensions
            )
            enhanced_variations.append(enhanced_var)
        # # 5. 主题分类
        # print("🎨 进行主题分类...")
        # enhanced_variations = []
        # for i, var in enumerate(unique_enhanced_variations):
        #     theme = await classify_theme(var.keyword)
        #     guided_method = None
        #     guided_2nd_level_method = None
            
        #     if var.method == 1:  # GUIDED模式
        #         original_var = agent4_result.variations[i] if i < len(agent4_result.variations) else None
        #         if original_var and hasattr(original_var, 'dimensions') and original_var.dimensions:
        #             dimension_index = i % len(original_var.dimensions)
        #             dimension = original_var.dimensions[dimension_index]
        #             guided_method, guided_2nd_level_method = get_guided_method_mapping(dimension)
            
        #     enhanced_var = EnhancedVariation(
        #         id=f"m{i+1:02d}",
        #         field=var.field,
        #         keyword=var.keyword,
        #         dataFact=var.dataFact,
        #         theme=theme,
        #         method="guided" if var.method == 1 else "blind",
        #         guidedmethod=guided_method,
        #         guided2ndLevelMethod=guided_2nd_level_method,
        #         rNorm=0.0,
        #         thumb=generate_thumb_url(var.keyword),
        #         mapping_spec=None,
        #         dimensions=current_dimensions
        #     )
        #     enhanced_variations.append(enhanced_var)
        
        # 4.5. 主题均衡后处理(确保每个主题至少有指定数量的结果)
        print("🎯 进行主题均衡处理...")
        original_keyword = input_data.boundField.field
        enhanced_variations = await balance_themes(enhanced_variations, original_keyword, context_description, input_data.totalLimit)
        
        # 4.6. 智能截断(主题均衡后)
        if len(enhanced_variations) > input_data.totalLimit:
            print(f"🎯 智能截断：从 {len(enhanced_variations)} 个变体截断到 {input_data.totalLimit} 个")
            
            # 按主题分组
            theme_groups = {}
            for var in enhanced_variations:
                if var.theme not in theme_groups:
                    theme_groups[var.theme] = []
                theme_groups[var.theme].append(var)
            
            # 计算每主题应该保留的数量
            MIN_PER_THEME = max(1, input_data.totalLimit // 5)
            MAX_PER_THEME = MIN_PER_THEME + 1  # 允许每个主题最多比最小值多1个
            print(f"🎯 每主题最小保留数量: {MIN_PER_THEME}, 最大保留数量: {MAX_PER_THEME}")
            
            # 按主题均衡分配，不区分来源
            final_variations = []
            remaining_slots = input_data.totalLimit
            
            # 按主题分组所有变体
            all_theme_groups = {}
            for var in enhanced_variations:
                if var.theme not in all_theme_groups:
                    all_theme_groups[var.theme] = []
                all_theme_groups[var.theme].append(var)
            
            # 为每个主题分配最小数量
            for theme in ['Nature', 'Artifact', 'Body', 'Life', 'Others']:
                if theme in all_theme_groups and remaining_slots > 0:
                    theme_vars = all_theme_groups[theme]
                    # 优先选择主题均衡生成的变体(method="blind" 且 guidedmethod=None)
                    balanced_vars = [v for v in theme_vars if v.method == "blind" and v.guidedmethod is None]
                    original_vars = [v for v in theme_vars if not (v.method == "blind" and v.guidedmethod is None)]
                    
                    # 先添加主题均衡生成的变体
                    for var in balanced_vars[:MIN_PER_THEME]:
                        if remaining_slots > 0:
                            final_variations.append(var)
                            remaining_slots -= 1
                    
                    # 如果还不够，从原有变体中补充
                    current_count = len([v for v in final_variations if v.theme == theme])
                    still_needed = MIN_PER_THEME - current_count
                    if still_needed > 0 and remaining_slots > 0:
                        for var in original_vars[:min(still_needed, remaining_slots)]:
                            if remaining_slots > 0:
                                final_variations.append(var)
                                remaining_slots -= 1
            
            # 如果还有剩余位置，按主题均衡填充
            if remaining_slots > 0:
                # 计算每个主题的当前数量
                current_theme_counts = {}
                for var in final_variations:
                    current_theme_counts[var.theme] = current_theme_counts.get(var.theme, 0) + 1
                
                # 按主题轮流分配剩余位置，确保均衡且不超过最大数量
                theme_order = ['Nature', 'Artifact', 'Body', 'Life', 'Others']
                while remaining_slots > 0:
                    added_any = False
                    for theme in theme_order:
                        if remaining_slots <= 0:
                            break
                        if theme in all_theme_groups:
                            # 检查当前主题是否已达到最大数量
                            current_count = len([v for v in final_variations if v.theme == theme])
                            if current_count >= MAX_PER_THEME:
                                continue
                                
                            theme_vars = all_theme_groups[theme]
                            for var in theme_vars:
                                if var not in final_variations and remaining_slots > 0:
                                    final_variations.append(var)
                                    remaining_slots -= 1
                                    added_any = True
                                    break
                    
                    # 如果没有任何主题可以添加更多变体，跳出循环
                    if not added_any:
                        break
            
            # 确保严格达到目标数量
            if len(final_variations) < input_data.totalLimit:
                deficit = input_data.totalLimit - len(final_variations)
                print(f"🎯 智能截断后数量不足，需要补充 {deficit} 个变体")
                
                # 从所有变体中补充
                all_unused = []
                for var in enhanced_variations:
                    if var not in final_variations:
                        all_unused.append(var)
                
                for var in all_unused[:deficit]:
                    final_variations.append(var)
            
            enhanced_variations = final_variations
            balanced_count = len([v for v in final_variations if v.method == "blind" and v.guidedmethod is None])
            original_count = len(final_variations) - balanced_count
            print(f"🎯 智能截断完成：保留 {balanced_count} 个主题均衡变体，{original_count} 个原有变体")
            
            # 智能截断后去重
            seen_keywords = set()
            unique_variations = []
            for var in enhanced_variations:
                if var.keyword not in seen_keywords:
                    seen_keywords.add(var.keyword)
                    unique_variations.append(var)
                else:
                    print(f"🎯 智能截断去重：移除重复关键词 '{var.keyword}'")
            
            enhanced_variations = unique_variations
            print(f"🎯 智能截断去重完成：从 {len(final_variations)} 个变体去重到 {len(enhanced_variations)} 个")
            
            # 4. 如果去重后数量不足，需要补充
            if len(enhanced_variations) < input_data.totalLimit:
                deficit = input_data.totalLimit - len(enhanced_variations)
                print(f"🎯 去重后数量不足，需要补充 {deficit} 个变体")
                
                # 直接使用LLM补充缺失的变体
                try:
                    llm = ChatOpenAI(
                        model=os.getenv("BALANCE_THEME_LLM_MODEL", "gpt-4o-mini"),
                        temperature=0.5,
                        openai_api_key=os.getenv("OPENAI_API_KEY"),
                        openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
                    )
                    
                    def is_technical_term(keyword: str) -> bool:
                        # 文件扩展名
                        file_extensions = {
                            'json', 'xml', 'csv', 'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'mp4', 'avi', 'mov', 'wmv',
                            'mp3', 'wav', 'flac', 'aac', 'zip', 'rar', '7z', 'tar', 'gz', 'html', 'css', 'js',
                            'py', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'scala'
                        }
                        
                        # 技术术语
                        technical_terms = {
                            'api', 'url', 'http', 'https', 'sql', 'nosql', 'rest', 'graphql', 'oauth', 'jwt',
                            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'redis', 'mongodb', 'mysql', 'postgresql',
                            'react', 'vue', 'angular', 'nodejs', 'express', 'django', 'flask', 'spring', 'laravel',
                            'git', 'github', 'gitlab', 'jenkins', 'ci', 'cd', 'devops', 'microservice', 'serverless',
                            # 编程语言内置函数和关键字
                            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set', 'range',
                            'print', 'input', 'open', 'close', 'read', 'write', 'append', 'remove', 'pop',
                            'split', 'join', 'replace', 'strip', 'lower', 'upper', 'title', 'capitalize',
                            'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'import', 'from', 'return',
                            'try', 'except', 'finally', 'with', 'as', 'in', 'is', 'and', 'or', 'not',
                            'true', 'false', 'null', 'none', 'self', 'super', 'init', 'new', 'this'
                        }
                        
                        return keyword.lower() in file_extensions or keyword.lower() in technical_terms
                    
                    def is_spelling_error(keyword: str) -> bool:
                        # 常见的拼写错误
                        spelling_errors = {
                            'hourglas',  # 应该是 hourglass
                            'recieve',   # 应该是 receive
                            'seperate',  # 应该是 separate
                            'occured',   # 应该是 occurred
                            'definately', # 应该是 definitely
                            'accomodate', # 应该是 accommodate
                            'begining',  # 应该是 beginning
                            'calender',  # 应该是 calendar
                            'cemetary',  # 应该是 cemetery
                            'embarass',  # 应该是 embarrass
                            'existance', # 应该是 existence
                            'goverment', # 应该是 government
                            'independant', # 应该是 independent
                            'occassion', # 应该是 occasion
                            'priviledge', # 应该是 privilege
                            'rythm',     # 应该是 rhythm
                            'tommorrow', # 应该是 tomorrow
                            'untill',    # 应该是 until
                            'writting',  # 应该是 writing
                        }
                        
                        return keyword.lower() in spelling_errors
                    
                    # 计算每个主题的当前数量
                    current_theme_counts = {}
                    for var in enhanced_variations:
                        current_theme_counts[var.theme] = current_theme_counts.get(var.theme, 0) + 1
                    
                    # 找出需要补充的主题
                    need_fill = []
                    for theme in ['Nature', 'Artifact', 'Body', 'Life', 'Others']:
                        current = current_theme_counts.get(theme, 0)
                        needed = max(0, MIN_PER_THEME - current)
                        if needed > 0:
                            need_fill.append((theme, needed))
                    
                    for theme, needed in need_fill:
                        if deficit <= 0:
                            break
                            
                        actual_needed = min(needed, deficit)
                        print(f"🎯 为主题 '{theme}' 补充 {actual_needed} 个变体...")
                            
                        sys_prompt = (
                            "你是名词生成助手。给出若干英文普通名词，适合归类到给定主题(Nature/Artifact/Body/Life/Others)，"
                            "避免专有名词、复数、动词/形容词、与输入 field 形态相同，仅返回 JSON 数组。"
                        )
                        user_prompt = f"""field: {input_data.boundField.field}
        context: {context_description}
        target_theme: {theme}
        need: {actual_needed}
        """
                        resp = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
                        import json, re
                        text = (resp.content or "").strip()
                        print(f"🎯 LLM 响应: {text[:100]}...")
                        words = []
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, list):
                                words = [w for w in parsed if isinstance(w, str)]
                        except Exception:
                            words = re.findall(r"[A-Za-z][a-z]{2,}", text)
                        
                        # 过滤技术术语和拼写错误
                        filtered_words = []
                        for w in words:
                            if not is_technical_term(w.lower()):
                                # 检查拼写错误
                                if not is_spelling_error(w.lower()):
                                    filtered_words.append(w)
                                else:
                                    print(f"🎯 过滤拼写错误: '{w}'")
                            else:
                                print(f"🎯 过滤技术术语: '{w}'")
                        
                        words = filtered_words
                        print(f"🎯 解析出的词汇: {words}")
                            
                        for w in words[:actual_needed]:
                            if deficit > 0:
                                dup = EnhancedVariation(
                                    id=f"m{len(enhanced_variations) + 1:02d}",
                                    field=input_data.boundField.field,
                                    keyword=w.lower(),
                                    dataFact=enhanced_variations[0].dataFact if enhanced_variations else "",
                                    theme=theme,
                                    method="blind",
                                    guidedmethod=None,
                                    guided2ndLevelMethod=None,
                                    rNorm=0.0,
                                    thumb=generate_thumb_url(w),
                                    mapping_spec=None,
                                    dimensions=enhanced_variations[0].dimensions if enhanced_variations and enhanced_variations[0].dimensions else []
                                )
                                enhanced_variations.append(dup)
                                deficit -= 1
                                
                    print(f"🎯 补充完成：最终 {len(enhanced_variations)} 个变体")
                except Exception as e:
                    print(f"⚠️ 补充失败: {e}")
                
                # 如果补充后仍然不足，强制补充到目标数量
                if len(enhanced_variations) < input_data.totalLimit:
                    final_deficit = input_data.totalLimit - len(enhanced_variations)
                    print(f"🎯 强制补充：还需要 {final_deficit} 个变体")
                    
                    # 使用有意义的词汇补充
                    fallback_words = [
                        "wave", "tide", "storm", "bridge", "forest", "galaxy", "reef", "volcano", "desert", "oasis",
                        "compass", "mirror", "labyrinth", "canvas", "symphony", "beacon", "harbor", "river", "avalanche", "furnace",
                        "nebula", "aurora", "meadow", "archipelago", "crystal", "engine", "palette", "prism", "mosaic", "vine",
                        "seed", "meteor", "orbit", "quarry", "forge", "anchor", "lantern", "spring", "delta", "horizon",
                        "island", "canyon", "harvest", "lighthouse", "corridor", "cathedral", "tunnel", "fountain", "glacier"
                    ]
                    
                    for i in range(final_deficit):
                        # 选择一个未使用的词汇
                        word = fallback_words[i % len(fallback_words)]
                        # 确保不重复
                        while any(var.keyword == word for var in enhanced_variations):
                            word = fallback_words[(i + 1) % len(fallback_words)]
                            i += 1
                        
                        simple_var = EnhancedVariation(
                            id=f"m{len(enhanced_variations) + i + 1:02d}",
                            field=input_data.boundField.field,
                            keyword=word,
                            dataFact=enhanced_variations[0].dataFact if enhanced_variations else "",
                            theme="Others",
                            method="blind",
                            guidedmethod=None,
                            guided2ndLevelMethod=None,
                            rNorm=0.0,
                            thumb=generate_thumb_url(word),
                            mapping_spec=None,
                            dimensions=enhanced_variations[0].dimensions if enhanced_variations and enhanced_variations[0].dimensions else []
                        )
                        enhanced_variations.append(simple_var)
                    
                    print(f"🎯 强制补充完成：最终 {len(enhanced_variations)} 个变体")
        
        # 5. 最终严格截断确保数量
        if len(enhanced_variations) > input_data.totalLimit:
            print(f"🎯 最终截断：从 {len(enhanced_variations)} 个变体截断到 {input_data.totalLimit} 个")
            enhanced_variations = enhanced_variations[:input_data.totalLimit]
        
        # 5. 调用模块三批量生成图片(可跳过)
        print(f"🖼️ 调用模块三批量生成接口(共{len(enhanced_variations)}个变体)...")
        
        # 准备模块三的输入数据
        field1 = current_dimensions[0] if current_dimensions and len(current_dimensions) > 0 else ""
        field2 = current_dimensions[1] if current_dimensions and len(current_dimensions) > 1 else ""
        print(f"📐 使用dimensions: field1='{field1}', field2='{field2}'")
        
        variations_for_module3 = []
        for var in enhanced_variations:
            variations_for_module3.append({
                "id": var.id,
                "field": var.field,
                "keyword": var.keyword,
                "dataFact": var.dataFact,
                "method": 1 if var.method == "guided" else 0,
            })
        
        if variations_for_module3:
            print(f"📦 第一个variation示例: {variations_for_module3[0]}")
        # 如果设置了跳过图片生成，则直接使用占位图并跳过模块三
        # ✅ 优化1：根据变体数量动态调整并发数和超时
        total_variations = len(variations_for_module3)
        
        if os.getenv("SKIP_IMAGE_GEN", "false").lower() in ["1", "true", "yes"]:
            for var in enhanced_variations:
                var.thumb = generate_thumb_url(var.keyword)
                var.mapping_spec = None
            print("⏭️ 已根据 SKIP_IMAGE_GEN 跳过模块三图片生成")
            # 设置默认值，避免未定义变量
            max_concurrent = 5
            timeout_seconds = 0
        else:
            if total_variations <= 10:
                max_concurrent = 10
                timeout_seconds = 720  # 15分钟
            elif total_variations <= 20:
                max_concurrent = 20
                timeout_seconds = 1200  # 20分钟
            else:
                max_concurrent = 30
                timeout_seconds = 1800 # 30分钟
        
        print(f"⚙️ 配置: 并发数={max_concurrent}, 超时={timeout_seconds}秒")
        
        batch_request = {
            "variations": variations_for_module3,
            "field1": field1,
            "field2": field2,
            "context_description": context_description,
            "max_concurrent": max_concurrent  # ✅ 动态并发数
        }
        
        # ✅ 优化2：分批处理(如果变体数量超过30个)
        if total_variations > 30:
            print(f"📦 变体数量较多({total_variations})，启用分批处理...")
            await process_variations_in_batches(
                enhanced_variations,
                batch_request,
                context_description,
                timeout_seconds
            )
        else:
            # 正常批量处理
            try:
                async with aiohttp.ClientSession() as session:
                    url = "http://localhost:8000/api/v1/module3/generate-visualization-batch"
                    
                    print(f"📤 发送批量请求到模块三...")
                    
                    async with session.post(
                        url, 
                        json=batch_request, 
                        timeout=aiohttp.ClientTimeout(total=timeout_seconds)  # ✅ 动态超时
                    ) as response:
                        if response.status == 200:
                            batch_result = await response.json()
                            results = batch_result.get("results", [])
                            result_map = {r.get("variation_id"): r for r in results}
                            
                            # 更新每个variation的thumb和mapping_spec
                            for var in enhanced_variations:
                                result = result_map.get(var.id)
                                if result:
                                    if result.get("success"):
                                        var.thumb = result.get("image_url", generate_thumb_url(var.keyword))
                                        var.mapping_spec = result.get("mapping_spec")
                                        print(f"✅ {var.keyword} 图片生成成功")
                                    else:
                                        var.thumb = generate_thumb_url(var.keyword)
                                        var.mapping_spec = None
                                        print(f"⚠️ {var.keyword} 使用占位图: {result.get('error')}")
                                else:
                                    var.thumb = generate_thumb_url(var.keyword)
                                    var.mapping_spec = None
                        else:
                            print(f"❌ 模块三返回错误: HTTP {response.status}")
                            for var in enhanced_variations:
                                var.thumb = generate_thumb_url(var.keyword)
                                var.mapping_spec = None
                                
            except asyncio.TimeoutError:
                print(f"⏰ 批量生成超时，使用占位图")
                for var in enhanced_variations:
                    var.thumb = generate_thumb_url(var.keyword)
                    var.mapping_spec = None
            except Exception as e:
                print(f"❌ 批量生成异常: {e}")
                for var in enhanced_variations:
                    var.thumb = generate_thumb_url(var.keyword)
                    var.mapping_spec = None
        
        print("🎉 所有处理完成！")
        
        # 6. 计算语义距离和rNorm(保持不变)
        print("📏 计算语义距离...")
        original_keyword = input_data.boundField.field.lower()
        distances = []
        
        for var in enhanced_variations:
            distance = calculate_semantic_distance(original_keyword, var.keyword.lower())
            distances.append(distance)
        
        normalized_distances = normalize_distances(distances)
        
        for i, var in enumerate(enhanced_variations):
            var.rNorm = normalized_distances[i] if i < len(normalized_distances) else 0.5
        
        # 7. 计算链接(保持不变)
        print("🔗 计算主题链接...")
        links = []
        theme_groups = {}
        
        for var in enhanced_variations:
            if var.theme not in theme_groups:
                theme_groups[var.theme] = []
            theme_groups[var.theme].append(var)
        
        for theme, vars_in_theme in theme_groups.items():
            if len(vars_in_theme) >= 2:
                for i in range(len(vars_in_theme)):
                    for j in range(i + 1, len(vars_in_theme)):
                        var1, var2 = vars_in_theme[i], vars_in_theme[j]
                        distance = calculate_semantic_distance(var1.keyword, var2.keyword)
                        links.append(LinkInfo(
                            source=var1.id,
                            target=var2.id,
                            distance=distance
                        ))
        
        # 8. 定义主题颜色映射(保持不变)
        themes = [
            ThemeInfo(name="Nature", color="#0C91BE"),
            ThemeInfo(name="Artifact", color="#87C11A"),
            ThemeInfo(name="Body", color="#C183DC"),
            ThemeInfo(name="Life", color="#F19A64"),
            ThemeInfo(name="Others", color="#E1C769")
        ]
        
        print(f"✅ 生成完成：{len(enhanced_variations)} 个变体，{len(links)} 个链接")
        
        return MetaphorGenerationOutput(
            variations=enhanced_variations,
            links=links,
            themes=themes,
            message="隐喻生成完成"
        )
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        
        return MetaphorGenerationOutput(
            variations=[],
            links=[],
            themes=[
                ThemeInfo(name="Nature", color="#0C91BE"),
                ThemeInfo(name="Artifact", color="#87C11A"),
                ThemeInfo(name="Body", color="#C183DC"),
                ThemeInfo(name="Life", color="#F19A64"),
                ThemeInfo(name="Others", color="#E1C769")
            ],
            message=f"生成失败: {str(e)}"
        )


# ✅ 新增：分批处理函数
async def process_variations_in_batches(
    enhanced_variations: list,
    batch_request: dict,
    context_description: str,
    timeout_seconds: int,
    batch_size: int = 15
):
    """
    分批处理大量变体，避免超时
    """
    variations = batch_request["variations"]
    total = len(variations)
    
    for i in range(0, total, batch_size):
        batch_variations = variations[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"📦 处理第 {batch_num}/{total_batches} 批({len(batch_variations)}个变体)...")
        
        sub_batch_request = {
            **batch_request,
            "variations": batch_variations
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8000/api/v1/module3/generate-visualization-batch"
                
                async with session.post(
                    url,
                    json=sub_batch_request,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    if response.status == 200:
                        batch_result = await response.json()
                        results = batch_result.get("results", [])
                        result_map = {r.get("variation_id"): r for r in results}
                        
                        # 更新对应的变体
                        for var in enhanced_variations:
                            if var.id in result_map:
                                result = result_map[var.id]
                                if result.get("success"):
                                    var.thumb = result.get("image_url", generate_thumb_url(var.keyword))
                                    var.mapping_spec = result.get("mapping_spec")
                                else:
                                    var.thumb = generate_thumb_url(var.keyword)
                                    var.mapping_spec = None
                    else:
                        print(f"❌ 第{batch_num}批失败: HTTP {response.status}")
                        
        except Exception as e:
            print(f"❌ 第{batch_num}批异常: {e}")
            
        # 批次间短暂延迟，避免API限流
        if i + batch_size < total:
            await asyncio.sleep(2)