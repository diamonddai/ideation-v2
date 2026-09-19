# """
# 模块三API路由：预览图生成
# """

# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional, Dict, Any
# import asyncio
# import uuid
# from .module3_controller import Module3Controller
# from ..module2_metaphor_generation.constants import MetaphorMethod
# import logging

# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# router = APIRouter(tags=["模块三：预览图生成"])

# class VariationBatchInput(BaseModel):
#     """从模块二接收的批量输入"""
#     variations: List[Dict[str, Any]]  # 模块二生成的变体列表
#     field1: str  # 第一个数据字段
#     field2: str  # 第二个数据字段
#     context_description: str
#     max_concurrent: int = 3  # 并发限制

# class VariationBatchResult(BaseModel):
#     """每个变体的处理结果"""
#     variation_id: str
#     keyword: str
#     dataFact: str
#     success: bool
#     image_url: Optional[str] = None
#     image_prompt: Optional[str] = None
#     mapping_spec: Optional[dict] = None
#     error: Optional[str] = None

# # 添加批量输入输出模型
# class BatchItem(BaseModel):
#     """批量处理项"""
#     id: str  # 用于标识每个请求
#     field: str
#     field1: Optional[str] = None
#     field2: Optional[str] = None
#     keyword: str
#     data_fact: str
#     method: int = 1
#     context_description: str

# class Module3BatchInput(BaseModel):
#     """批量处理输入"""
#     items: List[BatchItem]
#     max_concurrent: int = 3  # 并发数限制

# class BatchResult(BaseModel):
#     """批量处理结果项"""
#     id: str
#     success: bool
#     image_url: Optional[str] = None
#     image_prompt: Optional[str] = None
#     mapping_spec: Optional[dict] = None
#     error: Optional[str] = None

# class Module3BatchOutput(BaseModel):
#     """批量处理输出"""
#     results: List[BatchResult]
#     total: int
#     succeeded: int
#     failed: int
# # class Module3Input(BaseModel):
# #     """模块三输入参数"""
# #     field: str  # 数据字段（本体）
# #     keyword: str  # 喻体关键词
# #     data_fact: str  # 数据特征
# #     method: int  # 0 = BLIND, 1 = GUIDED
# #     context_description: str  # 上下文描述
# #     style_context: str = "极简主义图表风格"  # 图像风格上下文
# class Module3Input(BaseModel):
#     """模块三输入参数"""
#     field: str
#     field1: Optional[str] = None
#     field2: Optional[str] = None
#     keyword: str
#     data_fact: str
#     method: int = 1
#     context_description: str
#     mapping_override: Optional[dict] = None   # 新增：前端可传修改后的 mapping_spec

# # class Module3Output(BaseModel):
# #     """模块三输出结果"""
# #     success: bool
# #     image_url: Optional[str] = None
# #     image_prompt: Optional[str] = None
# #     data_fact_caption: Optional[str] = None
# #     mapping: List[str] = []
# #     source: Optional[str] = None
# #     target: Optional[str] = None
# #     error: Optional[str] = None
# class Module3Output(BaseModel):
#     """模块三输出结果"""
#     success: bool
#     image_url: Optional[str] = None
#     image_prompt: Optional[str] = None
#     data_fact_caption: Optional[str] = None
#     mapping: List[str] = []
#     mapping_spec: Optional[dict] = None   # 新增：返回完整映射规范
#     source: Optional[str] = None
#     target: Optional[str] = None
#     error: Optional[str] = None


# # ✅ 新增：带重试的处理函数
# async def process_single_item_with_retry(
#     controller: Module3Controller,
#     item: BatchItem,
#     max_retries: int = 2
# ) -> BatchResult:
#     """
#     处理单个批量项（带重试机制）
#     """
#     for attempt in range(max_retries + 1):
#         try:
#             # 兼容处理
#             f1 = item.field1 or item.field
#             f2 = item.field2 or "时间"
            
#             result = controller.run(
#                 field=item.field,
#                 field1=f1,
#                 field2=f2,
#                 keyword=item.keyword,
#                 data_fact=item.data_fact,
#                 context_description=item.context_description,
#             )
            
#             if result.get("success"):
#                 return BatchResult(
#                     id=item.id,
#                     success=True,
#                     image_url=result.get("image_url"),
#                     image_prompt=result.get("design", {}).get("image_prompt"),
#                     mapping_spec=result.get("mapping", {})
#                 )
#             else:
#                 error_msg = result.get("error", "Unknown error")
#                 if attempt < max_retries:
#                     logger.warning(f"变体 {item.id} 失败（第{attempt+1}次尝试）: {error_msg}，正在重试...")
#                     await asyncio.sleep(2)  # 重试前等待2秒
#                     continue
#                 else:
#                     return BatchResult(
#                         id=item.id,
#                         success=False,
#                         error=f"重试{max_retries}次后仍失败: {error_msg}"
#                     )
                    
#         except Exception as e:
#             if attempt < max_retries:
#                 logger.warning(f"变体 {item.id} 异常（第{attempt+1}次尝试）: {str(e)}，正在重试...")
#                 await asyncio.sleep(2)
#                 continue
#             else:
#                 return BatchResult(
#                     id=item.id,
#                     success=False,
#                     error=f"重试{max_retries}次后仍异常: {str(e)}"
#                 )
    
#     # 理论上不会到这里
#     return BatchResult(
#         id=item.id,
#         success=False,
#         error="Unknown error after retries"
#     )


# @router.post("/generate-visualization-batch", response_model=Dict[str, Any])
# async def generate_visualization_batch(input_data: VariationBatchInput):
#     """
#     批量为模块二的变体生成预览图（优化版）
    
#     优化点：
#     1. 增加重试机制
#     2. 更长的超时时间（5分钟）
#     3. 更好的错误处理和日志
#     """
#     controller = Module3Controller()
#     results = []
    
#     # ✅ 优化1：根据变体数量动态调整并发和超时
#     total_variations = len(input_data.variations)
#     max_concurrent = min(input_data.max_concurrent, 8)  # 最多8个并发
    
#     # 创建信号量控制并发
#     semaphore = asyncio.Semaphore(max_concurrent)
    
#     logger.info(f"开始批量生成 {total_variations} 个预览图，并发数: {max_concurrent}")
    
#     async def process_variation(variation: Dict[str, Any]) -> VariationBatchResult:
#         """处理单个变体（带重试和更长超时）"""
#         async with semaphore:
#             variation_id = variation.get('id', str(uuid.uuid4())[:8])
#             keyword = variation.get('keyword', '')
#             data_fact = variation.get('dataFact', '')
            
#             # ✅ 改进的field1/field2处理逻辑
#             # 1. 优先使用variation自己的field1/field2
#             field1 = variation.get('field1') or None
#             field2 = variation.get('field2') or None
            
#             # 2. 如果variation没有，使用批量请求的全局field1/field2
#             if not field1:
#                 field1 = input_data.field1 or variation.get('field', '') or "数据维度1"
#             if not field2:
#                 field2 = input_data.field2 or "时间"  # 使用中文"时间"作为默认值
            
#             logger.info(f"🔧 变体 {variation_id}: field1='{field1}', field2='{field2}'")
                
#             try:
#                 # ✅ 优化2：增加超时到5分钟，添加重试逻辑
#                 max_retries = 2
#                 for attempt in range(max_retries + 1):
#                     try:
#                         result = await asyncio.wait_for(
#                             asyncio.to_thread(
#                                 controller.run,
#                                 field=variation.get('field', ''),
#                                 field1=field1,
#                                 field2=field2,
#                                 keyword=keyword,
#                                 data_fact=data_fact,
#                                 context_description=input_data.context_description
#                             ),
#                             timeout=300  # ✅ 5分钟超时（从180秒增加到300秒）
#                         )
                        
#                         if result.get("success"):
#                             image_url = result.get("image_url", "")
#                             if not image_url:
#                                 image_url = get_fallback_image(keyword)
                            
#                             logger.info(f"✅ 变体 {variation_id} ({keyword}) 生成成功")
#                             return VariationBatchResult(
#                                 variation_id=variation_id,
#                                 keyword=keyword,
#                                 dataFact=data_fact,
#                                 success=True,
#                                 image_url=image_url,
#                                 image_prompt=result.get("design", {}).get("image_prompt"),
#                                 mapping_spec=result.get("mapping", {})
#                             )
#                         else:
#                             error_msg = result.get("error", "Generation failed")
#                             if attempt < max_retries:
#                                 logger.warning(f"⚠️ 变体 {variation_id} 失败（第{attempt+1}次），正在重试: {error_msg}")
#                                 await asyncio.sleep(2)  # 重试前等待
#                                 continue
#                             else:
#                                 logger.error(f"❌ 变体 {variation_id} 重试{max_retries}次后仍失败: {error_msg}")
#                                 return VariationBatchResult(
#                                     variation_id=variation_id,
#                                     keyword=keyword,
#                                     dataFact=data_fact,
#                                     success=False,
#                                     image_url=get_fallback_image(keyword),
#                                     error=f"重试{max_retries}次后失败: {error_msg}"
#                                 )
                                
#                     except asyncio.TimeoutError:
#                         if attempt < max_retries:
#                             logger.warning(f"⏰ 变体 {variation_id} 超时（第{attempt+1}次），正在重试...")
#                             await asyncio.sleep(2)
#                             continue
#                         else:
#                             logger.error(f"⏰ 变体 {variation_id} 重试{max_retries}次后仍超时")
#                             return VariationBatchResult(
#                                 variation_id=variation_id,
#                                 keyword=keyword,
#                                 dataFact=data_fact,
#                                 success=False,
#                                 image_url=get_fallback_image(keyword),
#                                 error=f"重试{max_retries}次后仍超时（5分钟）"
#                             )
                    
#             except Exception as e:
#                 logger.error(f"❌ 变体 {variation_id} 发生异常: {str(e)}")
#                 return VariationBatchResult(
#                     variation_id=variation_id,
#                     keyword=keyword,
#                     dataFact=data_fact,
#                     success=False,
#                     image_url=get_fallback_image(keyword),
#                     error=str(e)
#                 )
    
#     # 并发处理所有变体
#     tasks = [process_variation(var) for var in input_data.variations]
#     results = await asyncio.gather(*tasks, return_exceptions=False)
    
#     # 统计
#     succeeded = sum(1 for r in results if r.success)
#     failed = len(results) - succeeded
    
#     logger.info(f"批量生成完成: 成功 {succeeded}/{len(results)}")
    
#     return {
#         "results": [r.dict() for r in results],
#         "total": len(results),
#         "succeeded": succeeded,
#         "failed": failed,
#         "summary": f"成功生成 {succeeded}/{len(results)} 个预览图"
#     }


# def get_fallback_image(keyword: str) -> str:
#     """根据关键词生成占位图URL"""
#     fallback_images = {
#         "nature": "https://via.placeholder.com/512x512/10B981/FFFFFF?text=Nature+Metaphor",
#         "artifact": "https://via.placeholder.com/512x512/3B82F6/FFFFFF?text=Artifact+Metaphor",
#         "body": "https://via.placeholder.com/512x512/F59E0B/FFFFFF?text=Body+Metaphor",
#         "life": "https://via.placeholder.com/512x512/EC4899/FFFFFF?text=Life+Metaphor",
#         "default": "https://via.placeholder.com/512x512/6B7280/FFFFFF?text=Data+Visualization"
#     }
    
#     keyword_lower = keyword.lower()
#     if any(word in keyword_lower for word in ['tree', 'ocean', 'mountain', 'river']):
#         return fallback_images["nature"]
#     elif any(word in keyword_lower for word in ['tool', 'machine', 'building']):
#         return fallback_images["artifact"]
#     elif any(word in keyword_lower for word in ['heart', 'eye', 'hand']):
#         return fallback_images["body"]
#     elif any(word in keyword_lower for word in ['flower', 'seed', 'bird']):
#         return fallback_images["life"]
#     else:
#         return fallback_images["default"]


# # ✅ 保持原有的单个生成接口
# @router.post("/generate-visualization-one", response_model=Module3Output)
# async def generate_visualization_one(input_data: Module3Input) -> Module3Output:
#     """
#     生成单个预览图（用户调整映射后重新生成）
#     """
#     try:
#         f1 = input_data.field1
#         f2 = input_data.field2

#         controller = Module3Controller()
        
#         if input_data.mapping_override:
#             mapping_spec = input_data.mapping_override
#             design = controller.design_agent.run(mapping_spec)
#             image_url = controller._generate_image(design["image_prompt"])
            
#             channels_flat = []
#             for row in mapping_spec.get("defaultPlan", []):
#                 channels_flat.extend(row.get("channels", []))
#             mapping_list = sorted(list(set(channels_flat)))
            
#             return Module3Output(
#                 success=True,
#                 image_url=image_url,
#                 image_prompt=design.get("image_prompt"),
#                 data_fact_caption=design.get("data_fact_caption"),
#                 mapping=mapping_list,
#                 mapping_spec=mapping_spec,
#                 source=f1,
#                 target=input_data.keyword
#             )
#         else:
#             result = controller.run(
#                 field=input_data.field,
#                 field1=f1,
#                 field2=f2,
#                 keyword=input_data.keyword,
#                 data_fact=input_data.data_fact,
#                 context_description=input_data.context_description,
#             )

#             if not result.get("success"):
#                 return Module3Output(success=False, error=result.get("error", "未知错误"))

#             design = result.get("design", {})
#             mapping_spec = result.get("mapping", {})

#             channels_flat = []
#             for row in mapping_spec.get("defaultPlan", []):
#                 channels_flat.extend(row.get("channels", []))
#             mapping_list = sorted(list(set(channels_flat)))

#             return Module3Output(
#                 success=True,
#                 image_url=result.get("image_url"),
#                 image_prompt=design.get("image_prompt"),
#                 data_fact_caption=design.get("data_fact_caption"),
#                 mapping=mapping_list,
#                 mapping_spec=mapping_spec,
#                 source=f1,
#                 target=input_data.keyword
#             )

#     except Exception as e:
#         return Module3Output(
#             success=False,
#             error=f"模块三执行失败: {str(e)}"
#         )


# @router.post("/generate-visualization", response_model=Module3Output)
# async def generate_visualization(input_data: Module3Input) -> Module3Output:
#     """原有的单个生成接口（保持兼容）"""
#     return await generate_visualization_one(input_data)

"""
模块三API路由：预览图生成（完整版）
包含：标准流程、用户调整流程、批量生成
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from .module3_controller import Module3Controller
import logging
import concurrent.futures
from functools import partial

logger = logging.getLogger(__name__)
router = APIRouter(tags=["模块三：预览图生成"])


# ==================== 数据模型定义 ====================

class Module3Input(BaseModel):
    """单个生成输入"""
    field: str
    field1: Optional[str] = None
    field2: Optional[str] = None
    keyword: str
    data_fact: str
    method: int = 1
    context_description: str
    mapping_override: Optional[dict] = None


class Module3Output(BaseModel):
    """单个生成输出"""
    success: bool
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    data_fact_caption: Optional[str] = None
    mapping: List[str] = []
    mapping_spec: Optional[dict] = None
    source: Optional[str] = None
    target: Optional[str] = None
    error: Optional[str] = None


class VariationBatchInput(BaseModel):
    """批量生成输入"""
    variations: List[Dict[str, Any]]  # 模块二生成的变体列表
    field1: str  # 第一个数据字段
    field2: str  # 第二个数据字段
    context_description: str
    max_concurrent: int = 10


class VariationBatchResult(BaseModel):
    """批量生成单个结果"""
    variation_id: str
    keyword: str
    dataFact: str
    success: bool
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    mapping_spec: Optional[dict] = None
    error: Optional[str] = None


# ==================== 辅助函数 ====================

def get_fallback_image(keyword: str) -> str:
    """生成占位图URL"""
    fallback_images = {
        "nature": "https://via.placeholder.com/512x512/10B981/FFFFFF?text=Nature+Metaphor",
        "artifact": "https://via.placeholder.com/512x512/3B82F6/FFFFFF?text=Artifact+Metaphor",
        "body": "https://via.placeholder.com/512x512/F59E0B/FFFFFF?text=Body+Metaphor",
        "life": "https://via.placeholder.com/512x512/EC4899/FFFFFF?text=Life+Metaphor",
        "default": "https://via.placeholder.com/512x512/6B7280/FFFFFF?text=Data+Visualization"
    }
    
    keyword_lower = keyword.lower()
    if any(word in keyword_lower for word in ['tree', 'ocean', 'mountain', 'river']):
        return fallback_images["nature"]
    elif any(word in keyword_lower for word in ['tool', 'machine', 'building']):
        return fallback_images["artifact"]
    elif any(word in keyword_lower for word in ['heart', 'eye', 'hand']):
        return fallback_images["body"]
    elif any(word in keyword_lower for word in ['flower', 'seed', 'bird']):
        return fallback_images["life"]
    else:
        return fallback_images["default"]


# ==================== API 接口 ====================

@router.post("/generate-visualization-one", response_model=Module3Output)
async def generate_visualization_one(input_data: Module3Input) -> Module3Output:
    """
    生成单个预览图
    支持标准流程和用户调整映射
    """
    try:
        controller = Module3Controller()
        f1 = input_data.field1 or input_data.field
        f2 = input_data.field2 or "时间"
        
        # 用户调整映射流程
        if input_data.mapping_override:
            logger.info("🔄 用户调整映射模式")
            
            mapping_spec = input_data.mapping_override
            if "keyword" not in mapping_spec:
                mapping_spec["keyword"] = input_data.keyword
            if "dataFact" not in mapping_spec:
                mapping_spec["dataFact"] = input_data.data_fact
            if "contextDescription" not in mapping_spec:
                mapping_spec["contextDescription"] = input_data.context_description
            
            # 生成新prompt
            design = controller.design_agent.run(mapping_spec)
            image_url = controller._generate_image(design["image_prompt"], input_data.keyword)
            
            channels_flat = []
            for row in mapping_spec.get("defaultPlan", []):
                channels_flat.extend(row.get("channels", []))
            mapping_list = sorted(list(set(channels_flat)))
            
            return Module3Output(
                success=True,
                image_url=image_url,
                image_prompt=design.get("image_prompt"),
                data_fact_caption=design.get("data_fact_caption"),
                mapping=mapping_list,
                mapping_spec=mapping_spec,
                source=f1,
                target=input_data.keyword
            )
        
        # 标准自动生成流程
        else:
            logger.info("🎯 标准流程：自动生成最佳映射")
            
            result = controller.run(
                field=input_data.field,
                field1=f1,
                field2=f2,
                keyword=input_data.keyword,
                data_fact=input_data.data_fact,
                context_description=input_data.context_description,
            )

            if not result.get("success"):
                return Module3Output(success=False, error=result.get("error", "未知错误"))

            design = result.get("design", {})
            mapping_spec = result.get("mapping", {})

            channels_flat = []
            for row in mapping_spec.get("defaultPlan", []):
                channels_flat.extend(row.get("channels", []))
            mapping_list = sorted(list(set(channels_flat)))

            return Module3Output(
                success=True,
                image_url=result.get("image_url"),
                image_prompt=design.get("image_prompt"),
                data_fact_caption=design.get("data_fact_caption"),
                mapping=mapping_list,
                mapping_spec=mapping_spec,
                source=f1,
                target=input_data.keyword
            )

    except Exception as e:
        logger.error(f"❌ 单个生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return Module3Output(success=False, error=f"生成失败: {str(e)}")


# @router.post("/generate-visualization-batch", response_model=Dict[str, Any])
# async def generate_visualization_batch(input_data: VariationBatchInput):
#     """
#     批量生成预览图
    
#     优化：
#     - 并发控制
#     - 重试机制
#     - 超时处理
#     """
#     controller = Module3Controller()
#     total_variations = len(input_data.variations)
#     max_concurrent = min(input_data.max_concurrent, 10)
    
#     semaphore = asyncio.Semaphore(max_concurrent)
#     logger.info(f"开始批量生成 {total_variations} 个预览图，并发数: {max_concurrent}")
    
#     async def process_variation(variation: Dict[str, Any]) -> VariationBatchResult:
#         """处理单个变体"""
#         async with semaphore:
#             variation_id = variation.get('id', str(uuid.uuid4())[:8])
#             keyword = variation.get('keyword', '')
#             data_fact = variation.get('dataFact', '')
            
#             # 处理field1/field2
#             field1 = variation.get('field1') or input_data.field1 or variation.get('field', '') or "数据维度1"
#             field2 = variation.get('field2') or input_data.field2 or "时间"
            
#             logger.info(f"🔧 变体 {variation_id}: field1='{field1}', field2='{field2}'")
            
#             max_retries = 2
#             for attempt in range(max_retries + 1):
#                 try:
#                     result = await asyncio.wait_for(
#                         asyncio.to_thread(
#                             controller.run,
#                             field=variation.get('field', ''),
#                             field1=field1,
#                             field2=field2,
#                             keyword=keyword,
#                             data_fact=data_fact,
#                             context_description=input_data.context_description
#                         ),
#                         timeout=300  # 5分钟
#                     )
                    
#                     if result.get("success"):
#                         image_url = result.get("image_url", "") or get_fallback_image(keyword)
#                         logger.info(f"✅ 变体 {variation_id} ({keyword}) 生成成功")
#                         return VariationBatchResult(
#                             variation_id=variation_id,
#                             keyword=keyword,
#                             dataFact=data_fact,
#                             success=True,
#                             image_url=image_url,
#                             image_prompt=result.get("design", {}).get("image_prompt"),
#                             mapping_spec=result.get("mapping", {})
#                         )
#                     else:
#                         error_msg = result.get("error", "Generation failed")
#                         if attempt < max_retries:
#                             logger.warning(f"⚠️ 变体 {variation_id} 失败（第{attempt+1}次），重试...")
#                             await asyncio.sleep(2)
#                             continue
#                         else:
#                             logger.error(f"❌ 变体 {variation_id} 重试后仍失败")
#                             return VariationBatchResult(
#                                 variation_id=variation_id,
#                                 keyword=keyword,
#                                 dataFact=data_fact,
#                                 success=False,
#                                 image_url=get_fallback_image(keyword),
#                                 error=f"重试{max_retries}次后失败: {error_msg}"
#                             )
                            
#                 except asyncio.TimeoutError:
#                     if attempt < max_retries:
#                         logger.warning(f"⏰ 变体 {variation_id} 超时（第{attempt+1}次），重试...")
#                         await asyncio.sleep(2)
#                         continue
#                     else:
#                         logger.error(f"⏰ 变体 {variation_id} 超时")
#                         return VariationBatchResult(
#                             variation_id=variation_id,
#                             keyword=keyword,
#                             dataFact=data_fact,
#                             success=False,
#                             image_url=get_fallback_image(keyword),
#                             error="超时（5分钟）"
#                         )
                
#                 except Exception as e:
#                     if attempt < max_retries:
#                         logger.warning(f"❌ 变体 {variation_id} 异常（第{attempt+1}次），重试...")
#                         await asyncio.sleep(2)
#                         continue
#                     else:
#                         logger.error(f"❌ 变体 {variation_id} 异常: {str(e)}")
#                         return VariationBatchResult(
#                             variation_id=variation_id,
#                             keyword=keyword,
#                             dataFact=data_fact,
#                             success=False,
#                             image_url=get_fallback_image(keyword),
#                             error=str(e)
#                         )
    
#     # 并发处理
#     tasks = [process_variation(var) for var in input_data.variations]
#     results = await asyncio.gather(*tasks, return_exceptions=False)
    
#     # 统计
#     succeeded = sum(1 for r in results if r.success)
#     failed = len(results) - succeeded
    
#     logger.info(f"批量生成完成: 成功 {succeeded}/{len(results)}")
    
#     return {
#         "results": [r.dict() for r in results],
#         "total": len(results),
#         "succeeded": succeeded,
#         "failed": failed,
#         "summary": f"成功生成 {succeeded}/{len(results)} 个预览图"
#     }


# 修改 generate_visualization_batch 函数：
@router.post("/generate-visualization-batch", response_model=Dict[str, Any])
async def generate_visualization_batch(input_data: VariationBatchInput):
    """
    批量生成预览图 - 优化版
    
    关键优化：
    1. 使用 ProcessPoolExecutor 实现真正的并发
    2. 更激进的并发配置
    3. 快速失败机制
    """
    controller = Module3Controller()
    total_variations = len(input_data.variations)
    
    # ✅ 更激进的并发配置
    max_concurrent = min(input_data.max_concurrent, 30)  # 从10提高到30
    
    logger.info(f"🚀 开始批量生成 {total_variations} 个预览图，并发数: {max_concurrent}")
    
    # ✅ 使用进程池实现真正的并发（而不是受限的线程池）
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_concurrent)
    
    async def process_variation(variation: Dict[str, Any]) -> VariationBatchResult:
        """处理单个变体 - 优化版"""
        variation_id = variation.get('id', str(uuid.uuid4())[:8])
        keyword = variation.get('keyword', '')
        data_fact = variation.get('dataFact', '')
        
        field1 = variation.get('field1') or input_data.field1 or variation.get('field', '') or "数据维度1"
        field2 = variation.get('field2') or input_data.field2 or "时间"
        
        logger.info(f"🔧 变体 {variation_id}: field1='{field1}', field2='{field2}'")
        
        max_retries = 1  # ✅ 减少重试次数
        for attempt in range(max_retries + 1):
            try:
                # ✅ 使用进程池执行，真正的并发
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor,
                        partial(
                            controller.run,
                            field=variation.get('field', ''),
                            field1=field1,
                            field2=field2,
                            keyword=keyword,
                            data_fact=data_fact,
                            context_description=input_data.context_description
                        )
                    ),
                    timeout=300  # ✅ 降低超时时间到3分钟
                )
                
                if result.get("success"):
                    image_url = result.get("image_url", "") or get_fallback_image(keyword)
                    logger.info(f"✅ 变体 {variation_id} ({keyword}) 生成成功")
                    return VariationBatchResult(
                        variation_id=variation_id,
                        keyword=keyword,
                        dataFact=data_fact,
                        success=True,
                        image_url=image_url,
                        image_prompt=result.get("design", {}).get("image_prompt"),
                        mapping_spec=result.get("mapping", {})
                    )
                else:
                    error_msg = result.get("error", "Generation failed")
                    if attempt < max_retries:
                        logger.warning(f"⚠️ 变体 {variation_id} 失败（第{attempt+1}次），重试...")
                        await asyncio.sleep(1)  # ✅ 减少重试延迟
                        continue
                    else:
                        logger.error(f"❌ 变体 {variation_id} 重试后仍失败")
                        return VariationBatchResult(
                            variation_id=variation_id,
                            keyword=keyword,
                            dataFact=data_fact,
                            success=False,
                            image_url=get_fallback_image(keyword),
                            error=f"重试{max_retries}次后失败: {error_msg}"
                        )
                        
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    logger.warning(f"⏰ 变体 {variation_id} 超时（第{attempt+1}次），重试...")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"⏰ 变体 {variation_id} 超时")
                    return VariationBatchResult(
                        variation_id=variation_id,
                        keyword=keyword,
                        dataFact=data_fact,
                        success=False,
                        image_url=get_fallback_image(keyword),
                        error="超时（3分钟）"
                    )
            
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"❌ 变体 {variation_id} 异常（第{attempt+1}次），重试...")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"❌ 变体 {variation_id} 异常: {str(e)}")
                    return VariationBatchResult(
                        variation_id=variation_id,
                        keyword=keyword,
                        dataFact=data_fact,
                        success=False,
                        image_url=get_fallback_image(keyword),
                        error=str(e)
                    )
    
    try:
        # ✅ 真正的并发执行
        tasks = [process_variation(var) for var in input_data.variations]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # 统计
        succeeded = sum(1 for r in results if r.success)
        failed = len(results) - succeeded
        
        logger.info(f"✅ 批量生成完成: 成功 {succeeded}/{len(results)}")
        
        return {
            "results": [r.dict() for r in results],
            "total": len(results),
            "succeeded": succeeded,
            "failed": failed,
            "summary": f"成功生成 {succeeded}/{len(results)} 个预览图"
        }
    
    finally:
        # 清理进程池
        executor.shutdown(wait=False)

@router.post("/generate-visualization", response_model=Module3Output)
async def generate_visualization(input_data: Module3Input) -> Module3Output:
    """兼容旧版的接口"""
    return await generate_visualization_one(input_data)


@router.get("/test")
async def test_module3():
    """测试接口"""
    return {
        "message": "模块三：预览图生成模块运行正常",
        "status": "success",
        "available_endpoints": [
            "POST /module3/generate-visualization - 生成预览图（兼容旧版）",
            "POST /module3/generate-visualization-one - 生成单个预览图（支持修改映射）",
            "POST /module3/generate-visualization-batch - 批量生成预览图",
            "GET /module3/test - 测试接口"
        ]
    }

