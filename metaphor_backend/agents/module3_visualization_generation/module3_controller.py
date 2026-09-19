"""
模块三控制器：预览图生成
控制Agent6和Agent7的执行流程，调用文生图模型并存储到阿里云
迁移ApiImageGenerator的成功方案
"""
import os
import uuid
import requests
import base64
from io import BytesIO
from typing import Dict, Any
from .mapping_agent import MappingAgent
from .design_agent import DesignAgent
from ..module2_metaphor_generation.constants import MetaphorMethod
from PIL import Image
import time
import logging

logger = logging.getLogger(__name__)

class Module3Controller:
    def __init__(self):
        self.mapping_agent = MappingAgent()
        self.design_agent = DesignAgent()

        # 文生图API配置 - 使用ApiImageGenerator的成功配置
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.api_base_url = "https://api.nbai.art/v1"
        
        # 阿里云OSS配置（可选）
        self.access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
        self.access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        self.bucket_name = os.getenv('ALIYUN_OSS_BUCKET')
        self.endpoint = os.getenv('ALIYUN_OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')

    def run(self,
        field: str,
        field1: str,
        field2: str,
        keyword: str,
        data_fact: str,
        context_description: str,
    ) -> Dict[str, Any]:
        """
        模块三主流程：预览图生成
        """
        try:
            # Step 1: Agent6 - 构建映射规范
            mapping_spec = self.mapping_agent.run(
                field=field,
                field1=field1,
                field2=field2,
                keyword=keyword,
                data_fact=data_fact,
                context_description=context_description,
            )

            # Step 2: Agent7 - 生成图像提示词
            design = self.design_agent.run(mapping_spec)

            # Step 3: 文生图 - 使用优化的生成方案
            image_url = self._generate_image(design["image_prompt"], keyword)
            # Step 4: 返回结果
            return {
                "success": True,
                "mapping": mapping_spec,
                "design": design,
                "image_url": image_url,
            }
            
        except Exception as e:
            logger.error(f"模块三执行失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_image(self, image_prompt: str, keyword: str = "") -> str:
        """
        使用优化的方案生成图片（带重试机制）
        """
        max_retries = 1
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"文生图提示词（第{attempt+1}次尝试）: {image_prompt[:100]}...")
                
                # 检查API密钥
                if not self.openai_api_key:
                    logger.warning("⚠️ API密钥未设置，使用占位图")
                    return self._get_placeholder_image()
                
                # 调用文生图API
                image_url, image_data = self._call_api_like_generator(image_prompt)
                
                # OSS上传逻辑
                if self._oss_configured():
                    try:
                        filename = f"generated_images/{uuid.uuid4().hex}.jpg"
                        oss_url = self._upload_to_aliyun(image_data, filename)
                        logger.info(f"✅ 图片已上传到阿里云OSS: {oss_url}")
                        return oss_url
                    except Exception as oss_error:
                        logger.warning(f"⚠️ 阿里云OSS上传失败: {oss_error}")
                        logger.info("回退到直接返回API图片URL")
                        return image_url
                else:
                    logger.info("未配置阿里云OSS，直接返回API图片URL")
                    return image_url
                    
            except Exception as e:
                logger.error(f"❌ 图片生成失败（第{attempt+1}次尝试）: {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"⏳ 等待{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else: 
                    logger.warning("使用占位图，避免500错误")
                    return self._get_placeholder_image()
    

    def _call_api_like_generator(self, prompt: str) -> tuple[str, bytes]:
        """
        完全复制ApiImageGenerator的成功调用方式
        """
        try:
            # 临时清除环境变量中的代理设置
            old_http_proxy = os.environ.pop('HTTP_PROXY', None)
            old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
            old_http_proxy_lower = os.environ.pop('http_proxy', None)
            old_https_proxy_lower = os.environ.pop('https_proxy', None)
            
            try:
                url = f"{self.api_base_url}/images/generations"
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                }
                
                image_model = os.getenv('IMAGE_MODEL', 'gpt-image-1')
                image_quality = os.getenv('IMAGE_QUALITY', 'auto')
                
                data = {"model": image_model, "prompt": prompt, "n": 1}
                
                if image_model == "gpt-image-1":
                    data.update({
                        "size": "auto",  
                        "quality": image_quality if image_quality in ["high", "medium", "low", "auto"] else "auto",
                        "output_compression": 100,
                        "partial_images": 0,
                        "stream": False
                    })
                    print(f"使用 gpt-image-1 模型，质量: {image_quality}")
                    
                elif image_model == "dall-e-3":
                    data.update({
                        "size": "auto",
                        "quality": "standard",
                        "response_format": "b64_json"
                    })
                    print(f"使用 dall-e-3 模型")
                    
                else:
                    data.update({
                        "size": "auto",
                        "quality": image_quality,
                        "response_format": "b64_json"
                    })
                    print(f"使用 {image_model} 模型")
                
                print("正在调用文生图API...")
                print(f"请求参数: {data}")
                
                # 完全像ApiImageGenerator一样调用，不设置proxies参数
                response = requests.post(
                    url, 
                    headers=headers, 
                    json=data, 
                    timeout=300
                    # 不设置proxies参数！
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("API调用成功")
                    
                    # 处理返回的图片数据 - 复制ApiImageGenerator的逻辑
                    image_data_item = result["data"][0]
                    image_bytes = None
                    image_url = None
                    
                    # 优先处理 base64 数据
                    b64_data = image_data_item.get("b64_json")
                    if b64_data:
                        try:
                            image_bytes = base64.b64decode(b64_data)
                            # ✅ 优化：不再保存本地文件，直接返回
                            logger.info(f"✅ 图片数据获取成功，大小: {len(image_bytes)} bytes")
                            image_url = f"data:image/png;base64,{b64_data}"
                            
                        except Exception as e:
                            logger.error(f"❌ base64解码失败: {e}")
                            image_bytes = None
                        #     # 保存为本地图片文件
                        #     filename = f"generated_{uuid.uuid4().hex[:8]}.png"
                        #     file_path = os.path.join(os.getcwd(), filename)
                            
                        #     with open(file_path, 'wb') as f:
                        #         f.write(image_bytes)
                            
                        #     print("=" * 50)
                        #     print(f"图片已保存到: {file_path}")
                        #     print("双击文件即可查看图片")
                        #     print("=" * 50)
                            
                        #     image_url = f"data:image/png;base64,{b64_data}"
                        # except Exception as e:
                        #     print(f"base64解码失败: {e}")
                        #     image_bytes = None
                    
                    # 如果没有base64数据，尝试URL下载
                    if image_bytes is None:
                        image_url = image_data_item.get("url")
                        if image_url:
                            print(f"从URL下载图片: {image_url}")
                            img_response = requests.get(image_url, timeout=60)
                            if img_response.status_code == 200:
                                image_bytes = img_response.content
                            else:
                                raise Exception(f"图片下载失败: {img_response.status_code}")
                        else:
                            raise Exception("API返回中既没有base64数据也没有URL")
                    
                    if not image_bytes:
                        raise Exception("无法获取图片数据")
                    
                    print(f"图片数据获取成功，大小: {len(image_bytes)} bytes")
                    return image_url, image_bytes
                    
                else:
                    error_text = response.text
                    logger.error(f"❌ API调用失败: {response.status_code} - {error_text}")
                    raise Exception(f"API调用失败: {response.status_code} - {error_text}")
                    
            finally:
                # 恢复原始的代理设置
                if old_http_proxy is not None:
                    os.environ['HTTP_PROXY'] = old_http_proxy
                if old_https_proxy is not None:
                    os.environ['HTTPS_PROXY'] = old_https_proxy
                if old_http_proxy_lower is not None:
                    os.environ['http_proxy'] = old_http_proxy_lower
                if old_https_proxy_lower is not None:
                    os.environ['https_proxy'] = old_https_proxy_lower
                    
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            raise e 
    def _get_placeholder_image(self) -> str:
        """获取占位图"""
        placeholders = [
            "https://via.placeholder.com/512x512/3B82F6/FFFFFF?text=Chart+Preview",
            "https://via.placeholder.com/512x512/10B981/FFFFFF?text=Data+Visualization", 
            "https://via.placeholder.com/512x512/F59E0B/FFFFFF?text=Analytics+Preview"
        ]
        import random
        return random.choice(placeholders)
    
    def _oss_configured(self) -> bool:
        """检查OSS配置"""
        return all([
            self.access_key_id,
            self.access_key_secret, 
            self.bucket_name,
            self.endpoint
        ])
    
    def _upload_to_aliyun(self, image_data: bytes, filename: str) -> str:
        """上传图片到阿里云OSS"""
        try:
            import oss2
            
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
            
            result = bucket.put_object(filename, image_data)
            
            if result.status == 200:
                image_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{filename}"
                print(f"图片上传成功: {image_url}")
                return image_url
            else:
                raise Exception(f"阿里云OSS上传失败: {result.status}")
                
        except Exception as e:
            print(f"阿里云OSS上传失败: {str(e)}")
            raise e

# 版本v1
# from typing import Dict, Any
# from .mapping_agent import MappingAgent
# from .design_agent import DesignAgent
# from ..module2_metaphor_generation.constants import MetaphorMethod


# class Module3Controller:
#     def __init__(self):
#         self.mapping_agent = MappingAgent()
#         self.design_agent = DesignAgent()
    
#     def run(self, 
#             field: str,
#             keyword: str,
#             data_fact: str,
#             method: MetaphorMethod,
#             context_description: str,
#             style_context: str = "极简主义图表风格") -> Dict[str, Any]:
#         """
#         模块三主流程：预览图生成
        
#         Args:
#             field: 数据字段（本体）
#             keyword: 喻体关键词
#             data_fact: 数据特征
#             method: 隐喻方法（GUIDED/BLIND）
#             context_description: 上下文描述
#             style_context: 图像风格上下文
            
#         Returns:
#             Dict包含图片地址和相关信息
#         """
#         try:
#             # Step 1: Agent6 - 映射构建
#             print("开始执行Agent6: 映射构建")
#             mapping_result_list = self.mapping_agent.run(
#                 field=field,
#                 keyword=keyword,
#                 data_fact=data_fact,
#                 method=method,
#                 context_description=context_description
#             )
#             first_mapping = mapping_result_list[0]
#             # Step 2: Agent7 - 图像设计提示词生成
#             print("开始执行Agent7: 图像设计提示词生成")
#             design_result = self.design_agent.run(
#                 source=first_mapping["source"],
#                 target=first_mapping["target"],
#                 mapping=first_mapping["mapping"],
#                 data_fact=data_fact,
#                 style_context=style_context
#             )
            
#             # Step 3: 调用文生图模型（TODO）
#             print("开始调用文生图模型")
#             image_url = self._generate_image(design_result["image_prompt"])
            
#             # Step 4: 返回结果
#             return {
#                 "success": True,
#                 "image_url": image_url,
#                 "image_prompt": design_result["image_prompt"],
#                 "data_fact_caption": design_result["data_fact_caption"],
#                 "mapping": first_mapping["mapping"],
#                 "source": first_mapping["source"],
#                 "target": first_mapping["target"]
#             }
            
#         except Exception as e:
#             print(f"模块三执行失败: {str(e)}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "image_url": None,
#                 "image_prompt": None,
#                 "data_fact_caption": None,
#                 "mapping": [],
#                 "source": field,
#                 "target": keyword
#             }
    
#     def _generate_image(self, image_prompt: str) -> str:
#         """
#         调用文生图模型生成图片并存储到阿里云
        
#         Args:
#             image_prompt: 图像生成提示词
            
#         Returns:
#             图片URL地址
#         """
#         # TODO: 实现文生图模型调用（这部分 Ziang 来写，学姐不用写）
#         # 1. 调用稳定扩散模型或其他文生图API
#         # 2. 将生成的图片上传到阿里云OSS
#         # 3. 返回图片的URL地址
        
#         print(f"文生图提示词: {image_prompt}")
        
#         # 临时返回示例URL
#         return "https://example.com/generated_image.jpg"
    
#     def _upload_to_aliyun(self, image_data: bytes, filename: str) -> str:
#         """
#         上传图片到阿里云OSS
        
#         Args:
#             image_data: 图片数据
#             filename: 文件名
            
#         Returns:
#             阿里云OSS的URL地址
#         """
#         # TODO: 实现阿里云OSS上传
#         # 1. 配置阿里云OSS客户端
#         # 2. 上传图片数据
#         # 3. 返回可访问的URL
        
#         return f"https://oss.aliyun.com/bucket/{filename}" 