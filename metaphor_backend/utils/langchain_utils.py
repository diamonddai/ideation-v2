"""
LangChain 工具类 - 配置第三方 API 中转
"""

import os
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os

def create_llm(model_name: str = None, api_base: str = None, temperature: float = 0.3, max_tokens: int = 2000) -> ChatOpenAI:
    """
    创建配置了第三方 API 中转的 LLM 实例
    
    Args:
        model_name: 模型名称，默认使用配置文件中的设置
        
    Returns:
        ChatOpenAI: 配置好的 LLM 实例
    """
    if model_name is None:
        model_name = os.getenv("AGENT7_LLM_MODEL", "gpt-5-nano")
    # 优先使用参数 api_base，其次环境变量
    resolved_api_base = api_base or os.getenv("OPENAI_API_BASE") or "https://api.nbai.art/v1"
    return ChatOpenAI(
        model=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=resolved_api_base,
        temperature=temperature,
        max_tokens=max_tokens,
    )

def create_chain(prompt_template: str, model_name: str = None) -> LLMChain:
    """
    创建 LangChain 链
    
    Args:
        prompt_template: 提示词模板
        model_name: 模型名称
        
    Returns:
        LLMChain: 配置好的链实例
    """
    llm = create_llm(model_name)
    prompt = PromptTemplate.from_template(prompt_template)
    return LLMChain(llm=llm, prompt=prompt)

def test_api_connection() -> bool:
    """
    测试 API 连接是否正常
    
    Returns:
        bool: 连接是否成功
    """
    try:
        llm = create_llm()
        response = llm.invoke("Hello, this is a test message.")
        return True
    except Exception as e:
        print(f"API 连接测试失败: {e}")
        return False 