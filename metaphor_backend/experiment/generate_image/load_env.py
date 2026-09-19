#!/usr/bin/env python3
"""
环境变量加载脚本
支持从多个来源加载配置：.env文件、shell环境变量、~/.zshrc等
"""

import os
import subprocess
from pathlib import Path

def load_shell_env():
    """从shell环境加载变量"""
    try:
        # 获取当前shell的环境变量
        result = subprocess.run(['env'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            env_vars = {}
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
            return env_vars
    except Exception as e:
        print(f"加载shell环境变量失败: {e}")
    return {}

def load_zshrc_vars():
    """从~/.zshrc文件加载export的变量"""
    zshrc_path = Path.home() / '.zshrc'
    if not zshrc_path.exists():
        return {}
    
    env_vars = {}
    try:
        with open(zshrc_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('export ') and '=' in line:
                    # 解析 export KEY=value 格式
                    parts = line[7:].split('=', 1)  # 去掉 'export '
                    if len(parts) == 2:
                        key, value = parts
                        # 去掉可能的引号
                        value = value.strip('"\'')
                        env_vars[key] = value
    except Exception as e:
        print(f"读取~/.zshrc失败: {e}")
    
    return env_vars

def get_aliyun_config():
    """获取阿里云配置，优先从shell环境变量获取"""
    config = {}
    
    # 从shell环境变量获取
    shell_env = load_shell_env()
    zshrc_vars = load_zshrc_vars()
    
    # 合并环境变量
    all_env = {**zshrc_vars, **shell_env}
    
    # 查找阿里云相关配置
    aliyun_keys = [
        'ALIYUN_OSS_ACCESS_KEY_ID',
        'ALIYUN_OSS_ACCESS_KEY_SECRET', 
        'ALIYUN_OSS_ENDPOINT',
        'ALIYUN_OSS_BUCKET_NAME',
        'ALIYUN_OSS_REGION',
        # 可能的其他命名
        'ALIYUN_ACCESS_KEY_ID',
        'ALIYUN_ACCESS_KEY_SECRET',
        'OSS_ENDPOINT',
        'OSS_BUCKET_NAME',
        'OSS_REGION'
    ]
    
    for key in aliyun_keys:
        if key in all_env:
            config[key] = all_env[key]
    
    return config

def print_config_status():
    """打印配置状态"""
    print("=== 阿里云配置状态 ===")
    
    # 从多个来源获取配置
    aliyun_config = get_aliyun_config()
    
    if aliyun_config:
        print("✅ 找到阿里云配置:")
        for key, value in aliyun_config.items():
            if 'SECRET' in key or 'KEY' in key:
                display_value = value[:8] + '***' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f"  {key}: {display_value}")
    else:
        print("❌ 未找到阿里云配置")
        print("\n建议在~/.zshrc中添加以下配置:")
        print("export ALIYUN_OSS_ACCESS_KEY_ID='your_access_key_id'")
        print("export ALIYUN_OSS_ACCESS_KEY_SECRET='your_access_key_secret'")
        print("export ALIYUN_OSS_ENDPOINT='oss-cn-hangzhou.aliyuncs.com'")
        print("export ALIYUN_OSS_BUCKET_NAME='your_bucket_name'")
        print("export ALIYUN_OSS_REGION='cn-hangzhou'")
    
    return aliyun_config

if __name__ == "__main__":
    print_config_status() 