#!/usr/bin/env python3
"""
实验室环境启动脚本 - 检查环境并启动服务
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

def check_network():
    """检查网络连接"""
    try:
        import requests
        response = requests.get("https://api.nbai.art/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ 网络连接正常")
            return True
        else:
            print("⚠️  网络连接异常，但服务仍可启动")
            return True
    except Exception as e:
        print(f"⚠️  网络连接测试失败: {e}")
        print("在实验室环境中，可能需要配置代理或VPN")
        return True  # 不阻止启动

def main():
    """主函数"""
    print("🚀 启动 Metaphor Generation Backend (实验室环境)...")
    print("=" * 60)
    
    # 检查环境
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_env_file():
        print("请先配置环境变量文件")
        sys.exit(1)
    
    if not check_network():
        print("请检查网络配置")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ 环境检查通过，启动服务...")
    print("📍 服务将在 http://127.0.0.1:8000 启动")
    print("🔗 如果需要在局域网访问，请使用服务器IP地址")
    
    # 设置环境变量
    os.environ["HOST"] = "127.0.0.1"
    
    # 启动服务
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        print("💡 提示：在实验室环境中，可能需要:")
        print("   1. 检查防火墙设置")
        print("   2. 配置代理服务器")
        print("   3. 使用不同的端口")
        sys.exit(1)

if __name__ == "__main__":
    main()
