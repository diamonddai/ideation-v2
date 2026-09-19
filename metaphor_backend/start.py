#!/usr/bin/env python3
"""
启动脚本 - 检查环境并启动服务
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    print(f"✅ Python 版本: {sys.version}")
    return True

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import langchain
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_env_file():
    """检查环境变量文件"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  未找到 .env 文件")
        print("请创建 .env 文件并设置以下变量:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        print("OPENAI_API_BASE=https://api.nbai.art/v1")
        return False
    print("✅ 找到 .env 文件")
    return True

def check_api_connection():
    """检查 API 连接（可选）"""
    try:
        from utils.langchain_utils import test_api_connection
        if test_api_connection():
            print("✅ API 连接正常")
            return True
        else:
            print("⚠️  API 连接测试失败，但服务仍可启动")
            return True  # 不阻止启动
    except Exception as e:
        print(f"⚠️  API 连接测试跳过: {e}")
        return True  # 不阻止启动

def main():
    """主函数"""
    print("🚀 启动 Metaphor Generation Backend...")
    print("=" * 50)
    
    # 检查环境
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_env_file():
        print("请先配置环境变量文件")
        sys.exit(1)
    
    if not check_api_connection():
        print("请检查 API 配置")
        sys.exit(1)
    
    print("=" * 50)
    print("✅ 环境检查通过，启动服务...")
    
    # 启动服务
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 