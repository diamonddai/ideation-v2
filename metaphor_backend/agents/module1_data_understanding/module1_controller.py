# """
# 模块一：数据理解模块控制器
# 处理 CSV 上传并调用所有 Agent
# """

# from fastapi import APIRouter, UploadFile, File
# from pydantic import BaseModel
# from typing import List, Dict, Any
# import pandas as pd
# import io
# import json
# import logging

# # 导入各个 Agent
# from .header_semantic_agent import HeaderSemanticInput, HeaderSemanticOutput, header_semantic_agent
# from .data_pattern_agent import DataInsightInput, DataInsightOutput, data_insight_agent
# from .context_analysis_agent import FusionUnderstandingInput, FusionUnderstandingOutput, fusion_understanding_agent

# # 导入缓存工具
# from utils.cache_utils import cache

# # 创建模块日志器
# logger = logging.getLogger(__name__)

# router = APIRouter()

# class CSVUploadResponse(BaseModel):
#     boundFields: List[Dict[str, str]]
#     contextDescription: str
#     message: str

# @router.post("/upload-csv", response_model=CSVUploadResponse)
# async def upload_csv_and_analyze(file: UploadFile = File(...)):
#     """
#     上传 CSV 文件并进行完整的数据理解分析
#     - 调用 Agent1：表头语义分析
#     - 调用 Agent2：数据事实提取
#     - 调用 Agent3：数据-语义融合
#     - 返回 boundFields 给前端，保存 contextDescription 到缓存
#     """
#     try:
#         # 1. 读取 CSV 文件
#         content = await file.read()
#         df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
#         # 2. 提取表头
#         headers = df.columns.tolist()
        
#         # 3. 调用 Agent1：表头语义分析
#         logger.info("🔍 调用 Agent1：表头语义分析...")
#         agent1_input = HeaderSemanticInput(headers=headers)
#         agent1_result = await header_semantic_agent(agent1_input)
#         logger.debug(f"Agent1 结果: {len(agent1_result.semanticKeywords)} 个语义关键词")
        
#         # 4. 准备 Agent2 的输入数据
#         # 推断字段类型
#         field_types = {}
#         for col in df.columns:
#             if df[col].dtype in ['int64', 'float64']:
#                 field_types[col] = "数值型"
#             else:
#                 field_types[col] = "文本型"
        
#         # 获取样本数据
#         sample_data = df.head(10).to_dict('records')
        
#         # 5. 调用 Agent2：数据事实提取
#         logger.info("📊 调用 Agent2：数据事实提取...")
#         agent2_input = DataInsightInput(
#             fieldTypes=field_types,
#             sampleData=sample_data,
#         )
#         agent2_result = await data_insight_agent(agent2_input)
#         logger.debug(f"Agent2 结果: {len(agent2_result.dataFacts)} 个数据事实")
        
#         # 6. 调用 Agent3：数据-语义融合
#         logger.info("🔗 调用 Agent3：数据-语义融合...")
#         agent3_input = FusionUnderstandingInput(
#             semanticFields=agent1_result.semanticKeywords,
#             dataFacts=agent2_result.dataFacts
#         )
#         agent3_result = await fusion_understanding_agent(agent3_input)
#         logger.debug(f"Agent3 结果: {len(agent3_result.boundFields)} 个绑定字段")
        
#         # 7. 转换 boundFields 格式
#         bound_fields = [
#             {"field": item.field, "dataFact": item.dataFact}
#             for item in agent3_result.boundFields
#         ]
        
#         # 8. 返回结果
#         logger.info(f"✅ CSV分析完成，生成 {len(bound_fields)} 个绑定字段")
#         return CSVUploadResponse(
#             boundFields=bound_fields,
#             contextDescription=agent3_result.contextDescription,
#             message="数据分析完成"
#         )
        
#     except Exception as e:
#         # 错误处理
#         logger.error(f"❌ CSV处理失败: {str(e)}", exc_info=True)
#         error_context = f"CSV 处理失败: {str(e)}"
#         cache.set("contextDescription", error_context, expire_hours=24)
        
#         return CSVUploadResponse(
#             boundFields=[],
#             contextDescription=error_context,
#             message=f"处理失败: {str(e)}"
#         )

# @router.get("/get-context")
# async def get_context_description():
#     """获取缓存的 contextDescription"""
#     context = cache.get("contextDescription")
#     return {"contextDescription": context} 


"""
模块一：数据理解模块控制器
处理 CSV 上传并调用所有 Agent
"""

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import io
import json

# 导入各个 Agent
from .header_semantic_agent import HeaderSemanticInput, HeaderSemanticOutput, header_semantic_agent
from .data_pattern_agent import DataInsightInput, DataInsightOutput, data_insight_agent
from .context_analysis_agent import FusionUnderstandingInput, FusionUnderstandingOutput, fusion_understanding_agent

# 导入缓存工具
from utils.cache_utils import cache

router = APIRouter()

class CSVUploadResponse(BaseModel):
    boundFields: List[Dict[str, Any]]
    contextDescription: str
    message: str

@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_csv_and_analyze(file: UploadFile = File(...)):
    """
    上传 CSV 文件并进行完整的数据理解分析
    - 调用 Agent1：表头语义分析
    - 调用 Agent2：数据事实提取
    - 调用 Agent3：数据-语义融合
    - 返回 boundFields 给前端，保存 contextDescription 到缓存
    """
    try:
        # 1. 读取 CSV 文件
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # 2. 提取表头
        row_names = df.columns.tolist()  # 行名
        col_names = [str(i) for i in df.index.tolist()]  # 列名
        
        # 3. 调用 Agent1：表头语义分析
        print("🔍 调用 Agent1：表头语义分析...")
        print(col_names, row_names)
        agent1_input = HeaderSemanticInput(headers=row_names)
        agent1_result = await header_semantic_agent(agent1_input)
        
        # 4. 准备 Agent2 的输入数据
        # 推断字段类型
        field_types = {}
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                field_types[col] = "数值型"
            else:
                field_types[col] = "文本型"
        
        # 获取样本数据
        sample_data = df.head(10).to_dict('records')
        
        # 将整个文件内容转为 CSV 文本
        full_data = df.to_csv(index=False)
        
        # 5. 调用 Agent2：数据事实提取
        print("📊 调用 Agent2：数据事实提取...")
        agent2_input = DataInsightInput(
            fieldTypes=field_types,
            sampleData=sample_data,
            rowNames=row_names,  # 传递列名
            colNames=col_names,  # 传递行名
            fullData=full_data   # 传递完整文件内容
        )
        agent2_result = await data_insight_agent(agent2_input)
        
        # 6. 调用 Agent3：数据-语义融合
        print("🔗 调用 Agent3：数据-语义融合...")
        agent3_input = FusionUnderstandingInput(
            rowNames=row_names,
            semanticFields=agent1_result.semanticKeywords,
            dataFacts=agent2_result.dataFacts
        )
        agent3_result = await fusion_understanding_agent(agent3_input)
        
        # 7. 转换 boundFields 格式 - 使用字典，不是BoundFieldResponse
        bound_fields = []
        for item in agent3_result.boundFields:
            bound_fields.append({  # 👈 直接创建字典
                "field": item.field,
                "dataFact": item.dataFact,
                "dimensions": item.dimensions if hasattr(item, 'dimensions') else []
            })
        
        # 8. 保存到缓存
        cache.set("contextDescription", agent3_result.contextDescription, expire_hours=24)
        cache.set("boundFields", bound_fields, expire_hours=24)
        
        print(f"✅ 已保存 {len(bound_fields)} 个boundFields到缓存")
        # 在返回之前打印
        print("🔴 准备返回的 bound_fields:")
        for bf in bound_fields:
            print(f"  Field: {bf['field']}")
            print(f"    dimensions: {bf['dimensions']}")
            print(f"    len(dimensions): {len(bf['dimensions'])}")
            for i, dim in enumerate(bf['dimensions']):
                print(f"      [{i}]: '{dim}'")
        # 9. 返回结果
        return CSVUploadResponse(
            boundFields=bound_fields,  # 传递字典列表
            contextDescription=agent3_result.contextDescription,
            message="数据分析完成"
        )
        
    except Exception as e:
        # 错误处理
        import traceback
        traceback.print_exc()  # 打印完整错误堆栈
        
        error_context = f"CSV 处理失败: {str(e)}"
        cache.set("contextDescription", error_context, expire_hours=24)
        
        # 确保错误时也返回正确的响应对象
        return CSVUploadResponse(
            boundFields=[],
            contextDescription=error_context,
            message=f"处理失败: {str(e)}"
        )


@router.get("/get-context")
async def get_context_description():
    """获取缓存的 contextDescription"""
    context = cache.get("contextDescription")
    return {"contextDescription": context}