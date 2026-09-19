from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# 导入配置
from config import Config

# 导入各个模块的路由
from agents.module1_data_understanding import header_semantic_agent, data_pattern_agent, context_analysis_agent, module1_controller
from agents.module2_metaphor_generation import guided_metaphor_agent, blind_metaphor_agent, variation_planner_agent, feature_rewrite_agent, module2_controller
from agents.module3_visualization_generation import module3_router

# 导入日志配置
from logging_config import setup_advanced_logging

# 配置日志
logger = setup_advanced_logging(log_level=Config.LOG_LEVEL)

# 验证配置
try:
    Config.validate()
    logger.info("✅ 配置验证通过")
except ValueError as e:
    logger.error(f"❌ 配置验证失败: {e}")
    raise

app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册模块一的路由
app.include_router(header_semantic_agent.router, prefix="/api/v1/module1", tags=["数据理解模块"])
app.include_router(data_pattern_agent.router, prefix="/api/v1/module1", tags=["数据理解模块"])
app.include_router(context_analysis_agent.router, prefix="/api/v1/module1", tags=["数据理解模块"])
app.include_router(module1_controller.router, prefix="/api/v1/module1", tags=["数据理解模块"])

# 注册模块二的路由
app.include_router(guided_metaphor_agent.router, prefix="/api/v1/module2", tags=["隐喻生成模块"])
app.include_router(blind_metaphor_agent.router, prefix="/api/v1/module2", tags=["隐喻生成模块"])
app.include_router(variation_planner_agent.router, prefix="/api/v1/module2", tags=["隐喻生成模块"])
app.include_router(feature_rewrite_agent.router, prefix="/api/v1/module2", tags=["隐喻生成模块"])
app.include_router(module2_controller.router, prefix="/api/v1/module2", tags=["隐喻生成模块"])

# 注册模块三的路由
app.include_router(module3_router, prefix="/api/v1/module3", tags=["预览图生成模块"])

@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "Metaphor Generation Backend API",
        "version": "1.0.0",
        "modules": [
            "module1_data_understanding",
            "module2_metaphor_generation", 
            "module3_visualization_generation"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    ) 


@app.get("/api/health")
def health_api():
    # 别名，保持与前端 /api 前缀的约定
    return {"status": "healthy"}