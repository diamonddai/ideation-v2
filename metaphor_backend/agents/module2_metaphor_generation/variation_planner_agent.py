"""
Agent4：隐喻发散 Agent
整合 Guided 和 Blind 两种发散方法
"""

from pydantic import BaseModel
from fastapi import APIRouter
from typing import List, Dict, Any, Optional
import asyncio

# 导入其他 Agent 和常量
from .guided_metaphor_agent import guided_variation_agent, guided_variation_http, GuidedVariationInput, GuidedVariationOutput
from .blind_metaphor_agent import blind_variation_agent, blind_variation_http, BlindVariationInput, BlindVariationOutput
from .constants import GUIDED, BLIND

router = APIRouter()

class BoundField(BaseModel):
    field: str
    dataFact: str

class MetaphorVariation(BaseModel):
    field: str
    keyword: str
    dataFact: str
    method: int
    strategy: str = ""
    dimensions: List[str] = []
    original_keyword: str = ""

class VariationPlannerInput(BaseModel):
    boundField: BoundField
    contextDescription: Optional[str] = None
    blindRatio: float = 0.4  # 取值0~1，越大Blind占比越高
    totalLimit: int = 30     # 总量上限，默认30

class VariationPlannerOutput(BaseModel):
    variations: List[MetaphorVariation]

@router.post("/generate/all", response_model=VariationPlannerOutput)
async def variation_planner_agent(input_data: VariationPlannerInput) -> VariationPlannerOutput:
    """
    隐喻发散 Agent：
    - 作用：根据输入的 boundField 和 contextDescription，调用两类隐喻发散机制（Guided + Blind），并按比例整合其结果
    - 输入：绑定字段 + 上下文描述 + Blind 比例
    - 输出：整合后的隐喻变体列表
    """
    try:
        # 并行调用 Guided 和 Blind 方法（通过 HTTP 接口）
        print(f"[Agent4] 开始调用 guided 和 blind HTTP 接口")
        
        # 调用 Guided HTTP 接口
        print(f"[Agent4] 调用 guided_variation_http，keyword: {input_data.boundField.field}")
        guided_http_task = guided_variation_http(
            GuidedVariationInput(boundField=input_data.boundField.model_dump(), keyword=input_data.boundField.field)
        )
        # 调用 Blind HTTP 接口  
        print(f"[Agent4] 调用 blind_variation_http，field: {input_data.boundField.field}")
        blind_http_task = blind_variation_http(BlindVariationInput(boundField=input_data.boundField.model_dump()))
        
        # 等待两个任务完成
        guided_simple_result, blind_simple_result = await asyncio.gather(guided_http_task, blind_http_task)
        print(f"[Agent4] HTTP接口调用完成 - guided={len(guided_simple_result)}, blind={len(blind_simple_result)}")
        
        # 转换为内部格式
        print(f"[Agent4] 开始转换格式...")
        # 直接使用字典格式，避免 Pydantic 验证问题
        guided_variations = [
            {
                "field": item.field, 
                "keyword": item.keyword, 
                "dataFact": item.dataFact, 
                "method": GUIDED,
                "strategy": getattr(item, 'strategy', ''),
                "dimensions": getattr(item, 'dimensions', []),
                "original_keyword": getattr(item, 'original_keyword', '')
            }
            for item in guided_simple_result
        ]
        blind_variations = [
            {
                "field": item.field, 
                "keyword": item.keyword, 
                "dataFact": item.dataFact, 
                "method": BLIND,
                "strategy": "",
                "dimensions": [],
                "original_keyword": ""
            }
            for item in blind_simple_result
        ]
        print(f"[Agent4] 格式转换完成 - guided={len(guided_variations)}, blind={len(blind_variations)}")
        
        # 根据 blindRatio 与 totalLimit 进行配比裁剪
        guided_list = guided_variations or []
        blind_list = blind_variations or []

        # 兜底：若两侧皆为空，依据 dataFact 给出少量默认隐喻
        if not guided_list and not blind_list:
            df = (input_data.boundField.dataFact or "").lower()
            field = input_data.boundField.field
            candidates = []
            if any(k in df for k in ["increase", "grow", "rising", "up"]):
                candidates = ["flood", "tsunami", "avalanche"]
            elif any(k in df for k in ["decrease", "decline", "falling", "down"]):
                candidates = ["drought", "erosion", "sinkhole"]
            elif any(k in df for k in ["fluctuation", "volatile", "swing", "oscillation", "wave"]):
                candidates = ["wave", "tide", "whirlwind"]
            else:
                candidates = ["ocean", "landscape", "galaxy"]
            #             # ⚠️ 修改点1：改为创建字典而不是实例
            # blind_list = [
            #     {
            #         "field": field,
            #         "keyword": w,
            #         "dataFact": input_data.boundField.dataFact,
            #         "method": BLIND,
            #         "strategy": "",
            #         "dimensions": [],
            #         "original_keyword": ""
            #     }
            #     for w in candidates
            # ]
            # print(f"[Agent4] fallback generated {len(blind_list)} items by dataFact heuristic")
            blind_list = [
                {
                    "field": field,
                    "keyword": w,
                    "dataFact": input_data.boundField.dataFact,
                    "method": BLIND,
                    "strategy": "",
                    "dimensions": [],
                    "original_keyword": ""
                }
                for w in candidates
            ]
            print(f"[Agent4] fallback generated {len(blind_list)} items by dataFact heuristic")

        # 安全边界
        ratio = min(max(input_data.blindRatio, 0.0), 1.0)
        total = max(input_data.totalLimit, 0)
        if total == 0:
            # totalLimit=0 时返回空
            return VariationPlannerOutput(variations=[])

        # 计算各自配额
        blind_quota = int(round(total * ratio))
        guided_quota = total - blind_quota

        # 实际裁剪
        selected_guided = guided_list[:guided_quota]
        selected_blind = blind_list[:blind_quota]

        # 若一侧不足，用另一侧补齐
        deficit_guided = guided_quota - len(selected_guided)
        deficit_blind = blind_quota - len(selected_blind)
        if deficit_guided > 0 and len(blind_list) > len(selected_blind):
            selected_blind.extend(blind_list[len(selected_blind): len(selected_blind) + deficit_guided])
        if deficit_blind > 0 and len(guided_list) > len(selected_guided):
            selected_guided.extend(guided_list[len(selected_guided): len(selected_guided) + deficit_blind])

        # 合并输出，保持先 Guided 后 Blind 的顺序以增强可读性
        all_variations = selected_guided + selected_blind
        print(f"[Agent4] quotas guided={guided_quota}, blind={blind_quota}; selected guided={len(selected_guided)}, blind={len(selected_blind)}, total={len(all_variations)}")
        
        # 去重处理：基于 keyword 去重，保留第一个出现的变体
        seen_keywords = set()
        unique_variations = []
        for var in all_variations:
            if isinstance(var, MetaphorVariation):
                keyword = var.keyword
            else:
                keyword = var.get("keyword", "")
            
            if keyword not in seen_keywords:
                seen_keywords.add(keyword)
                unique_variations.append(var)
            else:
                print(f"[Agent4] 去重：移除重复关键词 '{keyword}'")
        
        print(f"[Agent4] 去重前: {len(all_variations)} 个变体，去重后: {len(unique_variations)} 个变体")
        
        # 转换为 MetaphorVariation 实例
        metaphor_variations = []
        for var in unique_variations:
            if isinstance(var, MetaphorVariation):
                metaphor_variations.append(var)
            else:
                metaphor_variations.append(MetaphorVariation(**var))

        # ✅ 严格限制：确保不超过 totalLimit
        if len(metaphor_variations) > total:
            print(f"[Agent4] 严格截断：从 {len(metaphor_variations)} 个变体截断到 {total} 个")
            metaphor_variations = metaphor_variations[:total]

        print(f"[Agent4] 最终返回 {len(metaphor_variations)} 个变体（限制：{total}）")
        return VariationPlannerOutput(variations=metaphor_variations)
        # # ⚠️ 修改点2：检查是否已经是MetaphorVariation实例
        # metaphor_variations = []
        # for var in all_variations:
        #     if isinstance(var, MetaphorVariation):
        #         # 如果已经是实例，直接添加
        #         metaphor_variations.append(var)
        #     elif isinstance(var, dict):
        #         # 如果是字典，创建实例
        #         metaphor_variations.append(MetaphorVariation(**var))
        #     else:
        #         print(f"[Agent4] 警告：未知类型 {type(var)}")

        # return VariationPlannerOutput(variations=metaphor_variations)

    except Exception as e:
        # 错误处理
        print(f"[Agent4] 异常: {e}")
        import traceback
        traceback.print_exc()
        return VariationPlannerOutput(variations=[])

@router.post("/generate/guided-only", response_model=VariationPlannerOutput)
async def guided_only_variation(input_data: VariationPlannerInput) -> VariationPlannerOutput:
    """
    仅调用 Guided 方法
    """
    try:
        guided_result = await guided_variation_agent(GuidedVariationInput(boundField=input_data.boundField))
        return VariationPlannerOutput(variations=guided_result.variations)
    except Exception as e:
        return VariationPlannerOutput(variations=[])

@router.post("/generate/blind-only", response_model=VariationPlannerOutput)
async def blind_only_variation(input_data: VariationPlannerInput) -> VariationPlannerOutput:
    """
    仅调用 Blind 方法
    """
    try:
        blind_result = await blind_variation_agent(BlindVariationInput(boundField=input_data.boundField))
        return VariationPlannerOutput(variations=blind_result.variations)
    except Exception as e:
        return VariationPlannerOutput(variations=[]) 