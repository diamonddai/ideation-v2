from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class DataUnderstandingResult(BaseModel):
    """数据理解结果模型"""
    keywords: List[str]
    context_description: str
    pattern_description: str
    trend_analysis: str
    business_context: str
    domain_insights: List[str]

class MetaphorResult(BaseModel):
    """隐喻结果模型"""
    metaphor_text: str
    confidence_score: float
    strategy_used: str
    reasoning: str

class VisualizationResult(BaseModel):
    """可视化结果模型"""
    image_prompt: str
    preview_description: str
    visual_elements: List[str]
    image_url: Optional[str] = None 