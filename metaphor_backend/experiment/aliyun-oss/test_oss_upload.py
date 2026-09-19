#!/usr/bin/env python3
"""
测试阿里云OSS上传功能
模仿模块三的文生图API调用和OSS上传流程
"""

import os
import uuid
import requests
import base64
from io import BytesIO
from dotenv import load_dotenv

# 加载环境变量 - 从项目根目录的.env文件加载
import sys
import os

# 加载环境变量
load_dotenv("/Users/anker/Tongji/idvx/project-code/Ideation_code/metaphor_backend/.env")
print(f"✅ 环境变量加载完成")

class OSSUploadTester:
    def __init__(self):
        # 文生图API配置 - 使用模块三的配置
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.api_base_url = "https://api.nbai.art/v1"
        
        # 阿里云OSS配置 - 使用模块三的环境变量名称
        self.access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
        self.access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        self.bucket_name = os.getenv('ALIYUN_OSS_BUCKET')
        self.endpoint = os.getenv('ALIYUN_OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')
        
        print("=" * 60)
        print("🔧 配置检查")
        print("=" * 60)
        print(f"OpenAI API Key: {'✅ 已设置' if self.openai_api_key else '❌ 未设置'}")
        print(f"阿里云 Access Key ID: {'✅ 已设置' if self.access_key_id else '❌ 未设置'}")
        print(f"阿里云 Access Key Secret: {'✅ 已设置' if self.access_key_secret else '❌ 未设置'}")
        print(f"阿里云 Bucket Name: {'✅ 已设置' if self.bucket_name else '❌ 未设置'}")
        print(f"阿里云 Endpoint: {self.endpoint}")
        
        # 检查所有环境变量
        print("\n🔍 环境变量详细检查:")
        env_vars = [
            'OPENAI_API_KEY',
            'ALIYUN_ACCESS_KEY_ID', 
            'ALIYUN_ACCESS_KEY_SECRET',
            'ALIYUN_OSS_BUCKET',
            'ALIYUN_OSS_ENDPOINT',
            # 尝试config.py中使用的变量名
            'ALIYUN_OSS_ACCESS_KEY_ID',
            'ALIYUN_OSS_ACCESS_KEY_SECRET', 
            'ALIYUN_OSS_BUCKET_NAME',
            'ALIYUN_OSS_REGION'
        ]
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # 隐藏敏感信息
                if 'KEY' in var or 'SECRET' in var:
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    display_value = value
                print(f"  {var}: {display_value}")
            else:
                print(f"  {var}: ❌ 未设置")
        
        # 尝试自动匹配阿里云配置
        print("\n🔧 尝试自动匹配阿里云配置:")
        aliyun_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID') or os.getenv('ALIYUN_OSS_ACCESS_KEY_ID')
        aliyun_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET') or os.getenv('ALIYUN_OSS_ACCESS_KEY_SECRET')
        aliyun_bucket = os.getenv('ALIYUN_OSS_BUCKET') or os.getenv('ALIYUN_OSS_BUCKET_NAME')
        aliyun_endpoint = os.getenv('ALIYUN_OSS_ENDPOINT')
        
        print(f"  匹配到的 Access Key ID: {'✅ 已找到' if aliyun_key_id else '❌ 未找到'}")
        print(f"  匹配到的 Access Key Secret: {'✅ 已找到' if aliyun_key_secret else '❌ 未找到'}")
        print(f"  匹配到的 Bucket Name: {'✅ 已找到' if aliyun_bucket else '❌ 未找到'}")
        print(f"  匹配到的 Endpoint: {aliyun_endpoint or '❌ 未找到'}")
        
        # 更新配置
        if aliyun_key_id:
            self.access_key_id = aliyun_key_id
        if aliyun_key_secret:
            self.access_key_secret = aliyun_key_secret
        if aliyun_bucket:
            self.bucket_name = aliyun_bucket
        if aliyun_endpoint:
            self.endpoint = aliyun_endpoint
        
        print("=" * 60)

    def _oss_configured(self) -> bool:
        """检查OSS配置"""
        return all([
            self.access_key_id,
            self.access_key_secret, 
            self.bucket_name,
            self.endpoint
        ])
    
    def test_network_connection(self):
        """测试网络连接"""
        print("🌐 测试网络连接...")
        try:
            # 测试基本网络连接
            response = requests.get("https://www.baidu.com", timeout=10, proxies={'http': None, 'https': None})
            print(f"✅ 基本网络连接正常，状态码: {response.status_code}")
            
            # 测试API服务器连接
            response = requests.get(f"{self.api_base_url}/models", 
                                  headers={"Authorization": f"Bearer {self.openai_api_key}"}, 
                                  timeout=10, 
                                  proxies={'http': None, 'https': None})
            print(f"✅ API服务器连接正常，状态码: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ 网络连接测试失败: {str(e)}")
            return False

    def _call_image_api(self, prompt: str) -> tuple[str, bytes]:
        """
        调用文生图API - 完全复制模块三的实现
        """
        try:
            print(f"🎨 文生图提示词: {prompt}")
            print(f"🌐 API基础URL: {self.api_base_url}")
            
            url = f"{self.api_base_url}/images/generations"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
            
            # 禁用代理
            proxies = {
                'http': None,
                'https': None
            }
            print(f"🔧 代理设置: {proxies}")
            
            # 使用模块三的模型和参数配置
            image_model = os.getenv('IMAGE_MODEL', 'gpt-image-1')
            image_quality = os.getenv('IMAGE_QUALITY', 'auto')
            
            data = {"model": image_model, "prompt": prompt, "n": 1}
            
            if image_model == "gpt-image-1":
                data.update({
                    "size": "512x512",
                    "quality": image_quality if image_quality in ["high", "medium", "low", "auto"] else "auto",
                    "output_compression": 100,
                    "partial_images": 0,
                    "stream": False
                })
                print(f"📱 使用模型: {image_model}")
                
            elif image_model == "dall-e-3":
                data.update({
                    "size": "512x512",
                    "quality": "standard",
                    "response_format": "b64_json"
                })
                print(f"📱 使用模型: {image_model}")
                
            else:
                data.update({
                    "size": "512x512",
                    "quality": image_quality,
                    "response_format": "b64_json"
                })
                print(f"📱 使用模型: {image_model}")
            
            print("🚀 正在调用文生图API...")
            print(f"📋 请求参数: {data}")
            print(f"🔗 请求URL: {url}")
            print(f"📤 请求头: {headers}")
            
            print("⏳ 发送HTTP请求...")
            response = requests.post(url, headers=headers, json=data, timeout=300, proxies=proxies)
            print(f"📥 收到响应，状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API调用成功")
                
                # 处理返回的图片数据
                image_data_item = result["data"][0]
                image_bytes = None
                image_url = None
                
                # 优先处理 base64 数据
                b64_data = image_data_item.get("b64_json")
                if b64_data:
                    try:
                        image_bytes = base64.b64decode(b64_data)
                        
                        # 保存为本地图片文件
                        filename = f"test_generated_{uuid.uuid4().hex[:8]}.png"
                        file_path = os.path.join(os.getcwd(), filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        print("=" * 50)
                        print(f"💾 图片已保存到: {file_path}")
                        print("👀 双击文件即可查看图片")
                        print("=" * 50)
                        
                        # 返回base64 URL给前端使用
                        image_url = f"data:image/png;base64,{b64_data}"
                        print("📄 获取到base64图片数据")
                    except Exception as e:
                        print(f"❌ base64解码失败: {e}")
                        image_bytes = None
                
                # 如果没有base64数据，尝试URL下载
                if image_bytes is None:
                    image_url = image_data_item.get("url")
                    if image_url:
                        print(f"🌐 从URL下载图片: {image_url}")
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            image_bytes = img_response.content
                        else:
                            raise Exception(f"图片下载失败: {img_response.status_code}")
                    else:
                        raise Exception("API返回中既没有base64数据也没有URL")
                
                if not image_bytes:
                    raise Exception("无法获取图片数据")
                
                print(f"📊 图片数据获取成功，大小: {len(image_bytes)} bytes")
                return image_url, image_bytes
                
            else:
                print(f"❌ API调用失败，状态码: {response.status_code}")
                print(f"📄 响应内容: {response.text}")
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ API调用异常: {str(e)}")
            print(f"🔍 异常类型: {type(e).__name__}")
            raise e

    def _upload_to_aliyun(self, image_data: bytes, filename: str) -> str:
        """
        上传图片到阿里云OSS - 完全复制模块三的实现
        """
        try:
            print(f"☁️ 开始上传到阿里云OSS...")
            print(f"📁 文件名: {filename}")
            
            import oss2
            
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
            
            result = bucket.put_object(filename, image_data)
            
            if result.status == 200:
                image_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{filename}"
                print(f"✅ 图片上传成功: {image_url}")
                return image_url
            else:
                raise Exception(f"阿里云OSS上传失败: {result.status}")
                
        except Exception as e:
            print(f"❌ 阿里云OSS上传失败: {str(e)}")
            raise e

    def test_full_workflow(self, prompt: str = "A minimalist chart showing population growth as an expanding ocean"):
        """
        测试完整流程：文生图API + 阿里云OSS上传
        """
        print("🎯 开始测试完整流程")
        print("=" * 60)
        
        try:
            # Step 1: 调用文生图API
            print("📝 Step 1: 调用文生图API")
            api_image_url, image_data = self._call_image_api(prompt)
            print(f"🔗 API返回的图片URL: {api_image_url}")
            print()
            
            # Step 2: 检查OSS配置
            print("📝 Step 2: 检查阿里云OSS配置")
            if self._oss_configured():
                print("✅ 阿里云OSS配置完整")
                
                # Step 3: 上传到阿里云OSS
                print("📝 Step 3: 上传到阿里云OSS")
                filename = f"test_images/{uuid.uuid4().hex}.jpg"
                oss_url = self._upload_to_aliyun(image_data, filename)
                print(f"🔗 阿里云OSS图片URL: {oss_url}")
                print()
                
                # 返回结果
                return {
                    "success": True,
                    "api_image_url": api_image_url,
                    "oss_image_url": oss_url,
                    "image_size": len(image_data)
                }
            else:
                print("❌ 阿里云OSS配置不完整，跳过上传")
                return {
                    "success": True,
                    "api_image_url": api_image_url,
                    "oss_image_url": None,
                    "image_size": len(image_data),
                    "message": "OSS配置不完整，仅返回API图片URL"
                }
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

def main():
    """主函数"""
    print("🧪 阿里云OSS上传测试工具")
    print("=" * 60)
    
    # 创建测试器
    tester = OSSUploadTester()
    
    # 测试网络连接
    print("\n📡 网络连接测试")
    print("-" * 40)
    network_ok = tester.test_network_connection()
    
    if not network_ok:
        print("⚠️ 网络连接有问题，但继续测试...")
    
    # 测试提示词
    test_prompt = "A minimalist chart showing population growth as an expanding ocean, clean vector graphics, abstract minimalism"
    
    # 执行测试
    result = tester.test_full_workflow(test_prompt)
    
    print("=" * 60)
    print("📊 测试结果")
    print("=" * 60)
    
    if result["success"]:
        print("✅ 测试成功!")
        print(f"🔗 API图片URL: {result['api_image_url']}")
        if result.get("oss_image_url"):
            print(f"☁️ OSS图片URL: {result['oss_image_url']}")
        print(f"📏 图片大小: {result['image_size']} bytes")
        if result.get("message"):
            print(f"ℹ️ 说明: {result['message']}")
    else:
        print("❌ 测试失败!")
        print(f"🚨 错误信息: {result['error']}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
