"""
本地缓存工具类
用于存储 contextDescription 等数据
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class LocalCache:
    """本地缓存类"""
    
    def __init__(self, cache_file: str = "cache.json"):
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """加载缓存数据"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载缓存失败: {e}")
        return {}
    
    def _save_cache(self):
        """保存缓存数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def set(self, key: str, value: Any, expire_hours: int = 24):
        """设置缓存"""
        expire_time = datetime.now() + timedelta(hours=expire_hours)
        self.cache_data[key] = {
            "value": value,
            "expire_time": expire_time.isoformat()
        }
        self._save_cache()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache_data:
            return None
        
        cache_item = self.cache_data[key]
        expire_time = datetime.fromisoformat(cache_item["expire_time"])
        
        if datetime.now() > expire_time:
            # 缓存已过期，删除
            del self.cache_data[key]
            self._save_cache()
            return None
        
        return cache_item["value"]
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache_data:
            del self.cache_data[key]
            self._save_cache()
    
    def clear(self):
        """清空缓存"""
        self.cache_data = {}
        self._save_cache()

# 全局缓存实例
cache = LocalCache() 