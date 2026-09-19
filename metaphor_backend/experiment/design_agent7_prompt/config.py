"""
Agent7 实验配置管理
集中管理所有参数，避免每次命令行修改
"""

import os
from typing import Optional

class Agent7Config:
    """Agent7 实验配置类"""
    
    # ===== Agent7 版本与行为配置 =====
    # 使用的 Agent7 版本：1, 2, 3, 4, 5
    AGENT7_VERSION: int = 5
    
    # 限制处理的输入条数（None 表示处理全部）
    AGENT7_LIMIT: Optional[int] = None  # 设为数字如 1, 3 来限制条数
    
    # 是否跳过生图（仅生成 prompt）
    AGENT7_SKIP_IMAGE: bool = False
    # AGENT7_SKIP_IMAGE: bool = False
    
    # ===== LLM 配置 =====
    # Agent7 使用的 LLM 模型
    AGENT7_LLM_MODEL: str = "gpt-5-nano"  # gpt-4o-mini, o4-mini, gpt-5-nano 等
    # AGENT7_LLM_MODEL: str = "o4-mini"  # o4-mini, gpt-5-nano 等
    
    # LLM API 基础地址
    LLM_API_BASE: str = "https://api.nbai.art/v1"
    
    # LLM 超时配置
    AGENT7_LLM_TIMEOUT: int = 25  # 秒
    AGENT7_LLM_RETRIES: int = 2
    AGENT7_LLM_BACKOFF: float = 1.5
    
    # ===== 文生图配置 =====
    # 文生图模型
    # IMAGE_MODEL: str = "dall-e-3"
    IMAGE_MODEL: str = "gpt-image-1"
    
    # 图片尺寸
    IMAGE_SIZE: str = "1024x1024"  # 1024x1024, 1792x1024, 1024x1792
    
    # 图片质量
    # IMAGE_QUALITY: str = "standard"  # standard, hd dall-e-3
    IMAGE_QUALITY: str = "low"  # standard, hd dall-e-3
    
    # 一次生成几张图片
    IMAGE_COUNT: int = 1
    
    # 图片 API 基础地址（通常与 LLM 相同）
    IMAGE_API_BASE: str = "https://api.nbai.art/v1"
    
    # ===== 输出配置 =====
    # 输出目录（相对于脚本的路径）
    OUTPUT_DIR: str = "outputs"
    
    # 是否在文件名中包含时间戳
    INCLUDE_TIMESTAMP: bool = True
    
    # 是否在文件名中包含模型版本
    INCLUDE_MODEL_VERSION: bool = True
    
    @classmethod
    def get_env_config(cls) -> dict:
        """将配置转换为环境变量字典"""
        return {
            "AGENT7_VERSION": str(cls.AGENT7_VERSION),
            "AGENT7_LIMIT": str(cls.AGENT7_LIMIT) if cls.AGENT7_LIMIT else None,
            "AGENT7_SKIP_IMAGE": "true" if cls.AGENT7_SKIP_IMAGE else "false",
            "AGENT7_LLM_MODEL": cls.AGENT7_LLM_MODEL,
            "LLM_API_BASE": cls.LLM_API_BASE,
            "AGENT7_LLM_TIMEOUT": str(cls.AGENT7_LLM_TIMEOUT),
            "AGENT7_LLM_RETRIES": str(cls.AGENT7_LLM_RETRIES),
            "AGENT7_LLM_BACKOFF": str(cls.AGENT7_LLM_BACKOFF),
            "IMAGE_MODEL": cls.IMAGE_MODEL,
            "IMAGE_SIZE": cls.IMAGE_SIZE,
            "IMAGE_QUALITY": cls.IMAGE_QUALITY,
            "IMAGE_COUNT": str(cls.IMAGE_COUNT),
            "IMAGE_API_BASE": cls.IMAGE_API_BASE,
            "OPENAI_API_BASE": cls.LLM_API_BASE,  # 兼容性
        }
    
    @classmethod
    def apply_to_env(cls):
        """将配置应用到环境变量"""
        config_dict = cls.get_env_config()
        for key, value in config_dict.items():
            if value is not None:
                os.environ[key] = value


# 预设配置方案
class Agent7Presets:
    """预设配置方案"""
    
    @classmethod
    def debug_mode(cls):
        """调试模式：只处理1条，跳过生图"""
        Agent7Config.AGENT7_LIMIT = 1
        Agent7Config.AGENT7_SKIP_IMAGE = True
        return Agent7Config
    
    @classmethod
    def fast_mode(cls):
        """快速模式：只处理1条，生成1张图"""
        Agent7Config.AGENT7_LIMIT = 1
        Agent7Config.AGENT7_SKIP_IMAGE = False
        Agent7Config.IMAGE_COUNT = 1
        return Agent7Config
    
    @classmethod
    def full_mode(cls):
        """完整模式：处理全部，生成3张图"""
        Agent7Config.AGENT7_LIMIT = None
        Agent7Config.AGENT7_SKIP_IMAGE = False
        Agent7Config.IMAGE_COUNT = 3
        return Agent7Config
    
    @classmethod
    def test_mode(cls):
        """测试模式：处理前3条，生成1张图"""
        Agent7Config.AGENT7_LIMIT = 3
        Agent7Config.AGENT7_SKIP_IMAGE = False
        Agent7Config.IMAGE_COUNT = 1
        return Agent7Config


# 默认配置实例
config = Agent7Config()
