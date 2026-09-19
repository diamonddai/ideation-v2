"""
Agent7 V5 - 基于v5中文指导原则的隐喻生成器

v5特点：
- 隐喻为结构，数据表达趋势即可，装饰最少
- 输出概念性视觉线稿（约30%完成度）
- 无坐标轴设计，以隐喻结构承载信息
- 给设计师保留70%的延展空间
"""

import os
import logging
import time
import httpx
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent7V5:
    """Agent7 V5版本 - 使用LLM生成prompt1"""
    
    def __init__(self):
        self.llm_model = os.getenv('AGENT7_LLM_MODEL', 'o4-mini')
        self.api_base = os.getenv('LLM_API_BASE', 'https://api.nbai.art/v1')
        self.timeout = int(os.getenv('AGENT7_LLM_TIMEOUT', '60'))  # 增加默认超时时间
        self.max_retries = int(os.getenv('AGENT7_LLM_RETRIES', '3'))  # 增加重试次数
        self.backoff_factor = float(os.getenv('AGENT7_LLM_BACKOFF', '2.0'))  # 调整退避因子
        
        # 创建HTTP客户端连接池
        self.http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,      # 连接超时
                read=self.timeout,  # 读取超时
                write=30.0,        # 写入超时
                pool=60.0          # 连接池超时
            ),
            limits=httpx.Limits(
                max_keepalive_connections=5,    # 保持连接数
                max_connections=10              # 最大连接数
            ),
            http2=True,  # 启用HTTP/2
            follow_redirects=True
        )
        
        # 初始化LLM（优化超时设置）
        self.llm = ChatOpenAI(
            model=self.llm_model,
            openai_api_base=self.api_base,
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            timeout=self.timeout,
            max_retries=0,  # 禁用LangChain内置重试，使用我们的智能重试
            http_client=self.http_client  # 使用自定义HTTP客户端
        )
        
        logger.info(f"[Agent7 v5] 初始化完成 - 模型: {self.llm_model}, API: {self.api_base}")
        logger.info(f"[Agent7 v5] 超时设置: {self.timeout}s, 重试: {self.max_retries}, 退避因子: {self.backoff_factor}")
    
    def generate_prompt1(self, prompt0: str) -> Optional[str]:
        """
        基于prompt0生成prompt1（带智能重试）
        
        Args:
            prompt0: 包含输入数据和v5设计原则的提示词
            
        Returns:
            prompt1: 用于文生图的详细提示词，或None如果生成失败
        """
        return self._generate_with_retry(prompt0)
    
    def _generate_with_retry(self, prompt0: str) -> Optional[str]:
        """智能重试机制"""
        system_message = SystemMessage(content="""你是一位专业的视觉隐喻设计师，专门负责将抽象的数据概念转换为精确的视觉隐喻提示词。

你的核心任务：
1. 深度理解输入数据：
   - keyword: 数据表中的核心字段，这是隐喻的载体
   - dataFact: 必须体现的关键数据事实，这是隐喻要传达的核心信息
   - contextDescription: 数据表的整体背景和上下文描述
   - defaultPlan: 严格遵循的数据维度与视觉映射通道规范

2. 严格遵循v5设计原则：隐喻为结构，数据表达趋势，装饰最少

3. 生成高质量的prompt1，确保可直接用于文生图API调用

输出标准：
- 生成完整、精确、可直接使用的prompt1
- 严格遵循v5设计原则
- 使用专业、清晰的英文表达
- 确保隐喻结构与数据映射关系明确""")
        
        human_message = HumanMessage(content=prompt0)
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"[Agent7 v5] 第{attempt + 1}次尝试 - 模型={self.llm_model} base={self.api_base}")
                
                # 调用LLM
                start_time = time.time()
                response = self.llm.invoke([system_message, human_message])
                elapsed_time = time.time() - start_time
                
                # 提取内容
                prompt1 = response.content.strip()
                
                if prompt1:
                    logger.info(f"[Agent7 v5] prompt1生成成功 (长度={len(prompt1)}, 耗时={elapsed_time:.2f}s)")
                    return prompt1
                else:
                    logger.warning(f"[Agent7 v5] 第{attempt + 1}次尝试返回空内容")
                    if attempt < self.max_retries:
                        wait_time = self.backoff_factor ** attempt
                        logger.info(f"[Agent7 v5] {wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("[Agent7 v5] 所有尝试都返回空内容")
                        return None
                        
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"[Agent7 v5] 第{attempt + 1}次尝试失败: {error_msg}")
                
                if attempt < self.max_retries:
                    # 智能退避策略
                    if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                        # 超时错误，使用指数退避
                        wait_time = self.backoff_factor ** attempt
                        logger.info(f"[Agent7 v5] 超时错误，{wait_time}秒后重试...")
                    elif "rate limit" in error_msg.lower() or "429" in error_msg:
                        # 限流错误，使用更长退避
                        wait_time = self.backoff_factor ** (attempt + 1)
                        logger.info(f"[Agent7 v5] 限流错误，{wait_time}秒后重试...")
                    else:
                        # 其他错误，使用标准退避
                        wait_time = self.backoff_factor ** attempt
                        logger.info(f"[Agent7 v5] 其他错误，{wait_time}秒后重试...")
                    
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"[Agent7 v5] 所有重试都失败了: {error_msg}")
                    return None
        
        return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取Agent7 V5的元数据"""
        return {
            "version": "v5",
            "llm": self.llm_model,  # 保持与其他版本一致的字段名
            "model": self.llm_model,
            "api_base": self.api_base,
            "description": "基于v5中文指导原则的隐喻生成器 - 隐喻为结构，概念性视觉线稿",
            "key_features": [
                "axes-less layout",
                "conceptual sketch (30% completion)", 
                "metaphor as structure",
                "trend over exact values",
                "minimal decoration"
            ]
        }
    
    def check_api_health(self) -> bool:
        """检查API健康状态"""
        try:
            # 使用连接池中的客户端进行健康检查
            response = self.http_client.get(f"{self.api_base}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"[Agent7 v5] API健康检查失败: {e}")
            return False
    
    def get_fallback_api(self) -> str:
        """获取备用API地址"""
        fallback_apis = [
            "https://api.nbai.art/v1"
        ]
        
        # 检查当前API是否健康
        if self.check_api_health():
            return self.api_base
        
        # 尝试备用API
        for api in fallback_apis:
            if api != self.api_base:
                try:
                    test_client = httpx.Client(timeout=5.0)
                    response = test_client.get(f"{api}/health")
                    test_client.close()
                    if response.status_code == 200:
                        logger.info(f"[Agent7 v5] 切换到备用API: {api}")
                        return api
                except:
                    continue
        
        logger.warning("[Agent7 v5] 所有API都不可用，使用当前API")
        return self.api_base
    
    def close(self):
        """关闭连接池，释放资源"""
        if hasattr(self, 'http_client'):
            self.http_client.close()
            logger.info("[Agent7 v5] HTTP客户端已关闭")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.close()


def create_agent7_v5() -> Agent7V5:
    """创建Agent7 V5实例"""
    return Agent7V5()
