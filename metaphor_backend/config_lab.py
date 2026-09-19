import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类 - 实验室环境版本"""
    
    # API 配置
    API_TITLE = "Metaphor Generation Backend"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "基于表格数据生成隐喻性图像提示词的多 Agent 系统"
    
    # 服务器配置 - 实验室环境使用localhost
    HOST = os.getenv("HOST", "127.0.0.1")  # 改为localhost避免DNS问题
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4")
    
    # 阿里云OSS配置
    ALIYUN_OSS_ACCESS_KEY_ID = os.getenv("ALIYUN_OSS_ACCESS_KEY_ID")
    ALIYUN_OSS_ACCESS_KEY_SECRET = os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET")
    ALIYUN_OSS_ENDPOINT = os.getenv("ALIYUN_OSS_ENDPOINT")
    ALIYUN_OSS_BUCKET_NAME = os.getenv("ALIYUN_OSS_BUCKET_NAME")
    ALIYUN_OSS_REGION = os.getenv("ALIYUN_OSS_REGION")
    
    # LangChain 配置
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    
    @classmethod
    def validate(cls):
        """验证必要的配置"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")
        
        return True
