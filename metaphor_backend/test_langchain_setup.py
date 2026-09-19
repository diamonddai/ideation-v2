#!/usr/bin/env python3
"""
LangChain 设置测试脚本
验证 LangChain 框架配置和 OpenAI API 连接
"""

from config import Config
from utils.langchain_utils import create_llm, create_chain

def test_langchain_setup():
    """测试 LangChain 设置"""
    print("🔧 LangChain 设置测试")
    print("=" * 50)
    
    print(f"OpenAI API Base: {Config.OPENAI_API_BASE}")
    print(f"Model: {Config.OPENAI_MODEL_NAME}")
    print(f"API Key: {'已设置' if Config.OPENAI_API_KEY else '未设置'}")
    
    try:
        # 创建 LLM 实例
        print("\n📡 创建 LLM 实例...")
        llm = create_llm()
        print("✅ LLM 实例创建成功")
        
        # 测试简单调用
        print("\n🧪 测试简单调用...")
        response = llm.invoke("请回复 'Hello World'")
        print(f"✅ 响应成功: {response.content}")
        
        # 测试 LangChain 链
        print("\n🔗 测试 LangChain 链...")
        prompt_template = "请分析以下数据字段：{headers}"
        chain = create_chain(prompt_template)
        
        test_headers = ["用户ID", "年龄", "收入"]
        result = chain.run(headers=test_headers)
        print(f"✅ 链执行成功: {result[:100]}...")
        
        print("\n🎉 所有测试通过！")
        print("LangChain 框架配置正确，可以正常使用 OpenAI API")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("请检查 API Key 和网络连接")

if __name__ == "__main__":
    test_langchain_setup() 