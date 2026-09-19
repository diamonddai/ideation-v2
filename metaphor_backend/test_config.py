#!/usr/bin/env python3
"""
配置测试脚本
"""

import os
from config import Config

def test_config():
    """测试配置是否正确加载"""
    print("🔧 配置测试")
    print("=" * 50)
    
    print(f"API Base URL: {Config.OPENAI_API_BASE}")
    print(f"Model Name: {Config.OPENAI_MODEL_NAME}")
    print(f"API Key: {'已设置' if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != 'your_openai_api_key_here' else '未设置'}")
    print(f"Host: {Config.HOST}")
    print(f"Port: {Config.PORT}")
    print(f"Debug: {Config.DEBUG}")
    
    print("\n✅ 配置加载成功！")
    print("\n📝 下一步：")
    print("1. 编辑 .env 文件，设置您的 API Key")
    print("2. 运行 python start.py 启动服务")
    print("3. 访问 http://localhost:8000/docs 查看 API 文档")

if __name__ == "__main__":
    test_config() 