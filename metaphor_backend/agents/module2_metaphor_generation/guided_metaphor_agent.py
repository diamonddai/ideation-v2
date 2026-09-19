from pydantic import BaseModel
from fastapi import APIRouter
from typing import List, Dict, Any, Optional
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
import os
import asyncio
import re
from enum import Enum


# 导入工具类和常量
from utils.langchain_utils import create_chain
from .constants import GUIDED

router = APIRouter()

# 在文件顶部，import语句之后添加
def clean_json_response(text: str) -> dict:
    """清理LLM响应并解析JSON"""
    # 移除<think></think>标签
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    
    # 处理markdown代码块
    if '```json' in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    elif '```' in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    
    # 找到JSON边界
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]
    
    return json.loads(text)
# 一级维度枚举 guidedMethod
class GuidedMethod(Enum):
    SEMANTIC = "语义维度"  # 语义关系类
    FUNCTIONAL = "功能维度"  # 功能行为类
    PERCEPTUAL = "感知维度"  # 感知特征类
    STRUCTURAL = "结构维度"  # 结构空间类

# 二级维度枚举 guided2ndLevelMethod
class DesignDimension(Enum):
    # 语义维度 (guidedMethod = SEMANTIC)
    CAUSAL_RELATION = "因果关系"  # guidedMethod = SEMANTIC
    CATEGORICAL_RELATION = "类属关系"  # guidedMethod = SEMANTIC
    SYMBOLIC_RELATION = "象征关系"  # guidedMethod = SEMANTIC
    
    # 功能维度 (guidedMethod = FUNCTIONAL)
    BEHAVIOR = "行为"  # guidedMethod = FUNCTIONAL
    USAGE = "用途"  # guidedMethod = FUNCTIONAL
    
    # 感知维度 (guidedMethod = PERCEPTUAL)
    COLOR = "颜色"  # guidedMethod = PERCEPTUAL
    SHAPE = "形状"  # guidedMethod = PERCEPTUAL
    SIZE = "尺寸"  # guidedMethod = PERCEPTUAL
    
    # 结构维度 (guidedMethod = STRUCTURAL)
    SPACE = "空间"  # guidedMethod = STRUCTURAL
    TIME = "时间"  # guidedMethod = STRUCTURAL

# 隐喻策略枚举
class MetaphorStrategy(Enum):
    SUBSTITUTE = "替代"
    COMBINE = "合并"
    ADAPT = "适应"
    MODIFY = "修改"
    REFRAME = "重构"
    REVERSE = "颠倒"

class BoundField(BaseModel):
    field: str
    dataFact: str

class MetaphorVariation(BaseModel):
    field: str
    keyword: str
    dataFact: str
    method: int = GUIDED
    strategy: str
    dimensions: List[str] = []
    original_keyword: str = ""

class GuidedVariationInput(BaseModel):
    boundField: BoundField
    keyword: str  # 英文名词原型

class GuidedVariationOutput(BaseModel):
    variations: List[MetaphorVariation]

class SimpleMetaphorItem(BaseModel):
    field: str
    keyword: str
    dataFact: str
    strategy: str = ""
    dimensions: List[str] = []
    original_keyword: str = ""

class SimpleGuidedOutput(BaseModel):
    variations: List[SimpleMetaphorItem]

class StrategyAgent:
    """单个策略Agent基类"""
    
    def __init__(self, strategy: MetaphorStrategy):
        self.strategy = strategy
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
        )
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        descriptions = {
            MetaphorStrategy.SUBSTITUTE: "替代策略：用相似概念替代原概念，保持核心语义",
            MetaphorStrategy.COMBINE: "合并策略：将原概念与其他概念组合，创造新的复合概念",
            MetaphorStrategy.ADAPT: "适应策略：让原概念适应不同场景或环境",
            MetaphorStrategy.MODIFY: "修改策略：修改原概念的属性、特征或状态",
            MetaphorStrategy.REFRAME: "重构策略：重新构建概念的关系或结构",
            MetaphorStrategy.REVERSE: "颠倒策略：反向思考，对立或相反的概念"
        }
        return descriptions.get(self.strategy, "")
    
    def get_dimension_selection_prompt(self, keyword: str) -> str:
        """生成维度选择提示词"""
        strategy_desc = self.get_strategy_description()
        return f"""
你是一个隐喻构思专家，使用{self.strategy.value}策略为关键词"{keyword}"选择最适合的3个设计维度。

策略描述：{strategy_desc}

维度分类：
- 语义维度：因果关系、类属关系、象征关系
- 功能维度：行为、用途
- 感知维度：颜色、形状、尺寸
- 结构维度：空间、时间

可选的10个维度：
1. 因果关系 (语义维度)
2. 类属关系 (语义维度)
3. 象征关系 (语义维度)
4. 行为 (功能维度)
5. 用途 (功能维度)
6. 颜色 (感知维度)
7. 形状 (感知维度)
8. 尺寸 (感知维度)
9. 空间 (结构维度)
10. 时间 (结构维度)

请根据"{keyword}"的语义特征和{self.strategy.value}策略的特点，选择3个最相关的维度。
注意：不同策略应该选择不同的维度组合，确保多样性。

返回JSON格式：
{{
    "selected_dimensions": ["维度1", "维度2", "维度3"],
    "reasoning": "选择理由"
}}
"""

    def get_metaphor_generation_prompt(self, keyword: str, dimensions) -> str:
        """生成隐喻构思提示词（强制英文单数名词输出）"""
        strategy_desc = self.get_strategy_description()
        dimensions_str = "、".join(dimensions)

        return f"""
You are a metaphor ideation expert. Using the {self.strategy.value} strategy, generate metaphor variations for the seed noun "{keyword}".

Strategy: {strategy_desc}
Selected dimensions: {dimensions_str}

Hard rules:
- All outputs MUST be English common nouns in singular form only (base lemma).
- No adjectives, no phrases, no hyphens, no punctuation, no numbers.
- For each selected dimension, produce 1-2 ideas.
- Each idea contains two hops: first and second metaphor.
- First hop: {keyword} -> noun_1 (single noun)
- Second hop: noun_1 -> noun_2 (single noun, deeper metaphor)

Diversity requirement:
- Try to include metaphors from different categories: Nature (ocean, mountain, tree), Artifact (tool, building, machine), Body (heart, eye, hand), Life (flower, bird, seed), and abstract concepts.
- Aim for a balanced mix of concrete and abstract metaphors.

Return ONLY JSON in this exact schema:
{{
  "metaphors": [
    {{
      "dimension": "string",
      "first_metaphor": "single_noun",
      "second_metaphor": "single_noun",
      "explanation": "short reasoning in English"
    }}
  ]
}}
"""

    async def select_dimensions(self, keyword: str):
        """选择最适合的3个维度"""
        # 为不同策略预设不同的维度组合，确保多样性
        # 每个策略的第一个维度都不同，确保guidedMethod的多样性
        strategy_dimensions = {
            MetaphorStrategy.SUBSTITUTE: ["因果关系", "类属关系", "象征关系"],  # 语义维度
            MetaphorStrategy.COMBINE: ["行为", "用途", "颜色"],  # 功能维度
            MetaphorStrategy.ADAPT: ["形状", "尺寸", "空间"],  # 感知维度
            MetaphorStrategy.MODIFY: ["时间", "象征关系", "行为"],  # 结构维度
            MetaphorStrategy.REFRAME: ["空间", "因果关系", "颜色"],  # 结构维度
            MetaphorStrategy.REVERSE: ["用途", "时间", "尺寸"]  # 功能维度
        }
        
        # 获取预设维度作为降级方案
        default_dimensions = strategy_dimensions.get(self.strategy, ["用途", "形状", "空间"])
        
        # 尝试使用LLM选择维度
        try:
            prompt = self.get_dimension_selection_prompt(keyword)
            messages = [
                SystemMessage(content="你是隐喻构思专家，请根据用户提示选择最合适的维度。"),
                HumanMessage(content=prompt)
            ]
            print(f"[StrategyAgent] 调用 LLM 选择维度，keyword: {keyword}, strategy: {self.strategy.value}")
            response = self.llm.invoke(messages)
            print(f"[StrategyAgent] LLM响应: {response.content.strip()}")
            # result = json.loads(response.content.strip())
            #修改点
            result = clean_json_response(response.content)
            selected = result.get("selected_dimensions", [])
            print(f"[StrategyAgent] LLM选择的维度: {selected}")
            
            # 验证选择的维度是否有效
            valid_dimensions = ["因果关系", "类属关系", "象征关系", "行为", "用途", "颜色", "形状", "尺寸", "空间", "时间"]
            if selected and all(dim in valid_dimensions for dim in selected):
                print(f"[StrategyAgent] LLM维度选择成功，使用LLM结果")
                return selected
            else:
                print(f"[StrategyAgent] LLM返回的维度无效，降级使用预设维度")
                return default_dimensions
                
        except Exception as e:
            print(f"[StrategyAgent] LLM维度选择失败: {e}")
            print(f"[StrategyAgent] 降级使用预设维度: {default_dimensions}")
            import traceback
            traceback.print_exc()
            return default_dimensions

    async def generate_metaphors(self, keyword: str, dimensions):
        """生成隐喻构思"""
        try:
            prompt = self.get_metaphor_generation_prompt(keyword, dimensions)
            messages = [
                SystemMessage(content="你是隐喻构思专家，请根据用户提示生成隐喻变体。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            # result = json.loads(response.content.strip())
            #修改点
            result = clean_json_response(response.content)
            return result.get("metaphors", [])
        except Exception as e:
            print(f"隐喻生成失败: {e}")
            return []

    async def run(self, keyword: str) -> List[MetaphorVariation]:
        """执行策略Agent"""
        # 1. 选择维度
        dimensions = await self.select_dimensions(keyword)
        
        # 2. 生成隐喻
        metaphors = await self.generate_metaphors(keyword, dimensions)
        
        # 3. 转换为MetaphorVariation格式
        variations = []

        def normalize_single_noun(word: str) -> str:
            if not isinstance(word, str):
                return ""
            w = word.strip().lower()
            for ch in [",", ".", "!", "?", ";", ":", "'", '"']:
                w = w.replace(ch, "")
            w = w.split()[0] if w.split() else w
            w = w.replace("-", "")
            if len(w) > 3 and w.endswith("ies"):
                w = w[:-3] + "y"
            elif len(w) > 2 and w.endswith("es"):
                w = w[:-2]
            elif len(w) > 1 and w.endswith("s"):
                w = w[:-1]
            return w

        for metaphor in metaphors:
            # 创建首次发散的变体
            first_variation = MetaphorVariation(
                field="",  # 由上层填充
                keyword=normalize_single_noun(metaphor.get("first_metaphor", "")),
                dataFact="",  # 由上层填充
                method=GUIDED,
                strategy=self.strategy.value,
                dimensions=dimensions,
                original_keyword=keyword
            )
            variations.append(first_variation)
            
            # 创建二次发散的变体
            second_variation = MetaphorVariation(
                field="",  # 由上层填充
                keyword=normalize_single_noun(metaphor.get("second_metaphor", "")),
                dataFact="",  # 由上层填充
                method=GUIDED,
                strategy=self.strategy.value,
                dimensions=dimensions,
                original_keyword=keyword
            )
            variations.append(second_variation)
        
        return variations

class GuidedVariationOrchestrator:
    """引导式变体编排器"""
    
    def __init__(self):
        self.strategy_agents = {
            MetaphorStrategy.SUBSTITUTE: StrategyAgent(MetaphorStrategy.SUBSTITUTE),
            MetaphorStrategy.COMBINE: StrategyAgent(MetaphorStrategy.COMBINE),
            MetaphorStrategy.ADAPT: StrategyAgent(MetaphorStrategy.ADAPT),
            MetaphorStrategy.MODIFY: StrategyAgent(MetaphorStrategy.MODIFY),
            MetaphorStrategy.REFRAME: StrategyAgent(MetaphorStrategy.REFRAME),
            MetaphorStrategy.REVERSE: StrategyAgent(MetaphorStrategy.REVERSE)
        }
    
    async def run_all_strategies(self, keyword: str) -> List[MetaphorVariation]:
        """运行所有策略Agent"""
        all_variations = []
        
        # 并行执行所有策略Agent
        tasks = []
        for strategy, agent in self.strategy_agents.items():
            task = agent.run(keyword)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        for i, result in enumerate(results):
            strategy_name = list(self.strategy_agents.keys())[i]
            if isinstance(result, Exception):
                print(f"策略 {strategy_name} 执行失败: {result}")
                continue
            print(f"策略 {strategy_name} 生成了 {len(result)} 个变体")
            all_variations.extend(result)
        
        # 去重处理：基于keyword去重，保留第一个出现的变体
        seen_keywords = set()
        unique_variations = []
        for variation in all_variations:
            if variation.keyword not in seen_keywords:
                seen_keywords.add(variation.keyword)
                unique_variations.append(variation)
            else:
                print(f"去重：移除重复关键词 '{variation.keyword}'")
        
        print(f"去重前: {len(all_variations)} 个变体，去重后: {len(unique_variations)} 个变体")
        return unique_variations

async def guided_variation_agent(input_data: GuidedVariationInput) -> GuidedVariationOutput:
    """
    Guided 隐喻发散 Agent：
    - 作用：使用六类隐喻构思策略对英文名词进行隐喻性拓展
    - 输入：绑定字段（field + dataFact）+ 英文关键词
    - 输出：多个隐喻变体，每个策略最多6个结果
    """
    try:
        # 创建编排器
        orchestrator = GuidedVariationOrchestrator()
        
        # 运行所有策略
        variations = await orchestrator.run_all_strategies(input_data.keyword)
        
        # 填充字段信息
        for variation in variations:
            variation.field = input_data.boundField.field
            variation.dataFact = input_data.boundField.dataFact
        
        # 控制输出数量（最多36个）
        if len(variations) > 36:
            variations = variations[:36]
        
        return GuidedVariationOutput(variations=variations)
        
    except Exception as e:
        print(f"引导式变体生成失败: {e}")
        # 返回默认结果
        default_variations = [
            MetaphorVariation(
                field=input_data.boundField.field,
                keyword="ocean",
                dataFact=input_data.boundField.dataFact,
                method=GUIDED,
                strategy="替代",
                dimensions=["用途", "形状", "空间"],
                original_keyword=input_data.keyword
            )
        ]
        return GuidedVariationOutput(variations=default_variations)

# 测试接口
@router.get("/test/strategies")
async def test_strategies():
    """测试所有策略Agent"""
    test_keyword = "education"
    orchestrator = GuidedVariationOrchestrator()
    variations = await orchestrator.run_all_strategies(test_keyword)
    
    return {
        "test_keyword": test_keyword,
        "total_variations": len(variations),
        "strategies_count": len(orchestrator.strategy_agents),
        "sample_variations": [
            {
                "keyword": v.keyword,
                "strategy": v.strategy,
                "dimensions": v.dimensions
            }
            for v in variations[:5]
        ]
    }

# HTTP 路由：/generate/guided 返回简化数组格式
@router.post("/generate/guided", response_model=List[SimpleMetaphorItem])
async def guided_variation_http(input_data: GuidedVariationInput) -> List[SimpleMetaphorItem]:
    try:
        core = await guided_variation_agent(input_data)
        # 核心函数已在内部限制最多36条
        simplified: List[SimpleMetaphorItem] = [
            SimpleMetaphorItem(
                field=v.field, 
                keyword=v.keyword, 
                dataFact=v.dataFact,
                strategy=v.strategy,
                dimensions=v.dimensions,
                original_keyword=v.original_keyword
            )
            for v in core.variations
        ]
        return simplified
    except Exception:
        return []

# 简化格式的 Guided 输出：仅 field/keyword/dataFact
@router.post("/generate/guided-simple", response_model=SimpleGuidedOutput)
async def guided_variation_agent_simple(input_data: GuidedVariationInput) -> SimpleGuidedOutput:
    try:
        base = await guided_variation_agent(input_data)
        simple_items: List[SimpleMetaphorItem] = []
        for v in base.variations:
            simple_items.append(SimpleMetaphorItem(field=v.field, keyword=v.keyword, dataFact=v.dataFact))
        return SimpleGuidedOutput(variations=simple_items)
    except Exception:
        return SimpleGuidedOutput(variations=[])

 