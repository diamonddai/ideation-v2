#!/usr/bin/env python3
"""
配置测试脚本
用于验证阿里云OSS配置是否正确
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import Config

def test_config():
    """测试配置"""
    print("=== 配置测试 ===")
    
    # 测试OpenAI配置
    print(f"OpenAI API Key: {'✅ 已设置' if Config.OPENAI_API_KEY else '❌ 未设置'}")
    print(f"OpenAI API Base: {Config.OPENAI_API_BASE}")
    
    # 测试阿里云OSS配置
    print(f"\n=== 阿里云OSS配置 ===")
    print(f"Access Key ID: {'✅ 已设置' if Config.ALIYUN_OSS_ACCESS_KEY_ID else '❌ 未设置'}")
    print(f"Access Key Secret: {'✅ 已设置' if Config.ALIYUN_OSS_ACCESS_KEY_SECRET else '❌ 未设置'}")
    print(f"Endpoint: {Config.ALIYUN_OSS_ENDPOINT or '❌ 未设置'}")
    print(f"Bucket Name: {Config.ALIYUN_OSS_BUCKET_NAME or '❌ 未设置'}")
    print(f"Region: {Config.ALIYUN_OSS_REGION or '❌ 未设置'}")
    
    # 检查环境变量
    print(f"\n=== 环境变量检查 ===")
    env_vars = [
        'OPENAI_API_KEY',
        'OPENAI_API_BASE', 
        'ALIYUN_OSS_ACCESS_KEY_ID',
        'ALIYUN_OSS_ACCESS_KEY_SECRET',
        'ALIYUN_OSS_ENDPOINT',
        'ALIYUN_OSS_BUCKET_NAME',
        'ALIYUN_OSS_REGION'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏敏感信息
            if 'KEY' in var or 'SECRET' in var:
                display_value = value[:8] + '***' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f"{var}: ✅ {display_value}")
        else:
            print(f"{var}: ❌ 未设置")
    
    # 验证配置
    print(f"\n=== 配置验证 ===")
    try:
        Config.validate()
        print("✅ 基础配置验证通过")
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
    
    # 检查阿里云OSS配置完整性
    oss_configs = [
        Config.ALIYUN_OSS_ACCESS_KEY_ID,
        Config.ALIYUN_OSS_ACCESS_KEY_SECRET,
        Config.ALIYUN_OSS_ENDPOINT,
        Config.ALIYUN_OSS_BUCKET_NAME
    ]
    
    if all(oss_configs):
        print("✅ 阿里云OSS配置完整")
    else:
        print("❌ 阿里云OSS配置不完整")
        print("请在.env文件中设置以下配置:")
        print("- ALIYUN_OSS_ACCESS_KEY_ID")
        print("- ALIYUN_OSS_ACCESS_KEY_SECRET")
        print("- ALIYUN_OSS_ENDPOINT")
        print("- ALIYUN_OSS_BUCKET_NAME")

if __name__ == "__main__":
    test_config() 