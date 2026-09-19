import os
import json
import base64
import requests
from datetime import datetime
import logging
from typing import Optional, Dict, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGenerator:
    """图片生成器，使用DALL-E模型生成图片并上传到阿里云OSS"""
    
    def __init__(self):
        self.openai_api_key = Config.OPENAI_API_KEY
        self.openai_api_base = Config.OPENAI_API_BASE
        self.oss_access_key_id = Config.ALIYUN_OSS_ACCESS_KEY_ID
        self.oss_access_key_secret = Config.ALIYUN_OSS_ACCESS_KEY_SECRET
        self.oss_endpoint = Config.ALIYUN_OSS_ENDPOINT
        self.oss_bucket_name = Config.ALIYUN_OSS_BUCKET_NAME
        self.oss_region = Config.ALIYUN_OSS_REGION
        
        # 创建本地保存目录
        self.local_save_dir = os.path.join(os.path.dirname(__file__), "generated_images")
        os.makedirs(self.local_save_dir, exist_ok=True)
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证必要的配置"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未设置")
        if not self.oss_access_key_id:
            raise ValueError("ALIYUN_OSS_ACCESS_KEY_ID 未设置")
        if not self.oss_access_key_secret:
            raise ValueError("ALIYUN_OSS_ACCESS_KEY_SECRET 未设置")
        if not self.oss_endpoint:
            raise ValueError("ALIYUN_OSS_ENDPOINT 未设置")
        if not self.oss_bucket_name:
            raise ValueError("ALIYUN_OSS_BUCKET_NAME 未设置")
    
    def generate_image_with_dalle(self, prompt: str, size: str = "1024x1024") -> Optional[Dict[str, Any]]:
        """使用DALL-E生成图片，返回完整的API响应数据"""
        try:
            url = f"{self.openai_api_base}/images/generations"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "size": size,
                "quality": "standard",
                "n": 1
            }
            
            logger.info(f"正在生成图片，提示词: {prompt[:100]}...")
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ 图片生成成功")
                logger.info(f"DALL-E API响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                logger.error(f"❌ 图片生成失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 图片生成异常: {str(e)}")
            return None
    
    def download_image(self, image_url: str) -> Optional[bytes]:
        """下载图片"""
        try:
            logger.info(f"正在下载图片: {image_url}")
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                image_data = response.content
                logger.info(f"✅ 图片下载成功，大小: {len(image_data)} bytes")
                return image_data
            else:
                logger.error(f"❌ 图片下载失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ 图片下载异常: {str(e)}")
            return None
    
    def save_image_locally(self, image_data: bytes, filename: str) -> str:
        """保存图片到本地"""
        try:
            filepath = os.path.join(self.local_save_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            logger.info(f"✅ 图片已保存到本地: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ 本地保存失败: {str(e)}")
            return ""
    
    def upload_to_oss(self, image_data: bytes, filename: str) -> Optional[str]:
        """上传图片到阿里云OSS"""
        try:
            import oss2
            
            # 创建OSS认证对象
            auth = oss2.Auth(self.oss_access_key_id, self.oss_access_key_secret)
            
            # 创建Bucket对象
            bucket = oss2.Bucket(auth, self.oss_endpoint, self.oss_bucket_name)
            
            # 上传文件
            logger.info(f"正在上传到OSS: {filename}")
            result = bucket.put_object(filename, image_data)
            
            if result.status == 200:
                # 构建访问URL
                oss_url = f"https://{self.oss_bucket_name}.{self.oss_endpoint}/{filename}"
                logger.info(f"✅ 图片上传成功: {oss_url}")
                return oss_url
            else:
                logger.error(f"❌ 图片上传失败: {result.status}")
                return None
                
        except ImportError:
            logger.error("❌ 请安装 oss2 库: conda install -c conda-forge oss2")
            return None
        except Exception as e:
            logger.error(f"❌ 图片上传异常: {str(e)}")
            return None
    
    def generate_and_save(self, prompt: str, filename_prefix: str = "generated_image") -> Dict[str, Any]:
        """生成图片并保存到本地和OSS"""
        result = {
            "success": False,
            "local_path": "",
            "oss_url": "",
            "dalle_response": None,
            "error": ""
        }
        
        try:
            # 生成图片
            dalle_response = self.generate_image_with_dalle(prompt)
            if not dalle_response:
                result["error"] = "DALL-E API调用失败"
                return result
            
            result["dalle_response"] = dalle_response
            
            # 获取图片URL
            image_url = dalle_response['data'][0]['url']
            revised_prompt = dalle_response['data'][0].get('revised_prompt', '')
            logger.info(f"修订后的提示词: {revised_prompt}")
            
            # 下载图片
            image_data = self.download_image(image_url)
            if not image_data:
                result["error"] = "图片下载失败"
                return result
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            
            # 保存到本地
            local_path = self.save_image_locally(image_data, filename)
            result["local_path"] = local_path
            
            # 上传到OSS
            oss_url = self.upload_to_oss(image_data, filename)
            result["oss_url"] = oss_url
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ 生成并保存图片失败: {str(e)}")
        
        return result

def test_image_generation():
    """测试图片生成功能"""
    # 从prompt.json中读取测试数据
    prompt_file = os.path.join(os.path.dirname(__file__), "prompt.json")
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except Exception as e:
        logger.error(f"❌ 读取prompt.json失败: {str(e)}")
        return
    
    # 创建图片生成器
    try:
        generator = ImageGenerator()
    except ValueError as e:
        logger.error(f"❌ 配置验证失败: {str(e)}")
        logger.info("请确保在.env文件中设置了以下配置:")
        logger.info("- ALIYUN_OSS_ACCESS_KEY_ID")
        logger.info("- ALIYUN_OSS_ACCESS_KEY_SECRET") 
        logger.info("- ALIYUN_OSS_ENDPOINT")
        logger.info("- ALIYUN_OSS_BUCKET_NAME")
        return
    
    # 测试前3个提示词
    test_count = min(3, len(test_data))
    # 测试最后一个提示
    # test_count = 1
    results = []
    
    for i, item in enumerate(test_data[:]): 
        if i < 3: # 总共5个，测试后两个数据
            continue
        # if i < len(test_data) - 1:# 测试最后一个数据时
        #     continue

        prompt = item.get("image_prompt", "")
        source = item.get("source", "")
        target = item.get("target", "")
        
        if not prompt:
            continue
            
        logger.info(f"\n=== 测试 {i+1}/{test_count} ===")
        logger.info(f"源域: {source}")
        logger.info(f"目标域: {target}")
        logger.info(f"提示词: {prompt[:100]}...")
        
        # 生成并保存图片
        filename_prefix = f"metaphor_{i+1}_{source.replace(' ', '_')}"
        save_result = generator.generate_and_save(prompt, filename_prefix)
        
        result = {
            "test_id": i + 1,
            "source": source,
            "target": target,
            "prompt": prompt,
            "local_path": save_result["local_path"],
            "oss_url": save_result["oss_url"],
            "success": save_result["success"],
            "error": save_result["error"],
            "dalle_response": save_result["dalle_response"]
        }
        results.append(result)
        
        if save_result["success"]:
            logger.info(f"✅ 成功生成图片:")
            logger.info(f"   本地路径: {save_result['local_path']}")
            logger.info(f"   OSS URL: {save_result['oss_url']}")
        else:
            logger.error(f"❌ 图片生成失败: {save_result['error']}")
    
    # 保存测试结果
    result_file = os.path.join(os.path.dirname(__file__), "test_results.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n=== 测试完成 ===")
    logger.info(f"成功: {sum(1 for r in results if r['success'])}/{len(results)}")
    logger.info(f"结果已保存到: {result_file}")
    logger.info(f"图片已保存到: {generator.local_save_dir}")

if __name__ == "__main__":
    test_image_generation() 