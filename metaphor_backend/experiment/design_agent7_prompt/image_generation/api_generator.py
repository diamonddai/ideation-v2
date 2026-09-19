import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import requests

import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiImageGenerator:
    """调用文生图 API（默认 DALL·E 兼容），仅本地保存，不上传 OSS。

    可通过参数或环境变量覆盖 api_base：
    - 优先使用 init(api_base)
    - 其次使用环境 IMAGE_API_BASE
    - 否则回退 Config.OPENAI_API_BASE
    """

    def __init__(self, output_dir: Optional[str] = None, api_base: Optional[str] = None) -> None:
        base_dir = output_dir or os.path.join(
            os.path.dirname(__file__), "..", "outputs"
        )
        self.output_dir = os.path.abspath(base_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("IMAGE_API_BASE") or "https://api.nbai.art/v1"

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未设置")
        if not self.api_base:
            raise ValueError("API Base 未设置（环境变量 IMAGE_API_BASE 或默认值）")

    def generate_image_with_dalle(self, prompt: str, size: str = "1024x1024", n: int = 1) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.api_base}/images/generations"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
            # 从环境变量获取模型和配置
            image_model = os.getenv('IMAGE_MODEL', 'gpt-image-1')
            image_quality = os.getenv('IMAGE_QUALITY', 'auto')
            
            # 根据模型设置不同的参数
            data = {"model": image_model, "prompt": prompt, "n": n}
            
            if image_model == "gpt-image-1":
                # gpt-image-1 支持的参数
                data.update({
                    "size": size if size in ["1024x1024", "1536x1024", "1024x1536", "auto"] else "auto",
                    "quality": image_quality if image_quality in ["high", "medium", "low", "auto"] else "auto",
                    # "background": "auto",  # transparent, opaque, auto
                    # "input_fidelity": "low",  # high, low
                    "output_compression": 100,  # 0-100%
                    "partial_images": 0,  # 0-3
                    "stream": False
                })
                # gpt-image-1 总是返回 base64，不需要 response_format
                logger.info(f"使用 gpt-image-1 模型，支持高级参数")
                
            elif image_model == "dall-e-3":
                # dall-e-2 支持的参数
                data.update({
                    "size": size if size in ["256x256", "512x512", "1024x1024"] else "1024x1024",
                    "quality": "standard",  # dall-e-3 只支持 standard
                    "response_format": "b64_json"  # 请求 base64 数据
                })
                logger.info(f"使用 dall-e-2 模型，标准参数")
                
            else:
                # 其他模型，使用通用参数
                data.update({
                    "size": size,
                    "quality": image_quality,
                    "response_format": "b64_json"
                })
                logger.info(f"使用 {image_model} 模型，通用参数")
            
            logger.info(f"请求生图 API: {url}")
            logger.info(f"请求参数: {data}")
            resp = requests.post(url, headers=headers, json=data, timeout=300)
            if resp.status_code == 200:
                result = resp.json()
                logger.info("✅ 图片生成成功")
                return result
            logger.error(f"❌ 图片生成失败: {resp.status_code} - {resp.text}")
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ 生图请求异常: {e}")
            return None

    def download_image(self, image_url: str) -> Optional[bytes]:
        try:
            logger.info(f"下载图片: {image_url}")
            resp = requests.get(image_url, timeout=30)
            if resp.status_code == 200:
                return resp.content
            logger.error(f"❌ 下载失败: {resp.status_code}")
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ 下载异常: {e}")
            return None

    def save_image(self, image_data: bytes, filename: str) -> str:
        path = os.path.join(self.output_dir, filename)
        with open(path, "wb") as f:
            f.write(image_data)
        return path

    def generate_and_save(self, prompt: str, filename_prefix: str = "generated_image", size: str = "1024x1024", agent7_model: str = "unknown") -> Dict[str, Any]:
        result: Dict[str, Any] = {"success": False, "local_path": None, "prompt_path": None, "error": None, "api_base": self.api_base}
        try:
            # 生成时间戳（精确到分钟）和模型版本
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            model_suffix = f"agent7_{agent7_model}"
            
            # 先保存 prompt 文本
            prompt_path = os.path.join(self.output_dir, f"{filename_prefix}_prompt_{ts}_{model_suffix}.txt")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)
            result["prompt_path"] = prompt_path

            # 从环境变量获取图片生成数量
            image_count = int(os.getenv('IMAGE_COUNT', '3'))
            dalle_resp = self.generate_image_with_dalle(prompt, size=size, n=image_count)
            if not dalle_resp:
                result["error"] = "API 调用失败"
                return result

            image_paths = []
            for i, image_data_item in enumerate(dalle_resp["data"]):
                image_bytes: Optional[bytes] = None
                try:
                    b64_data = image_data_item.get("b64_json")
                    if b64_data:
                        import base64
                        image_bytes = base64.b64decode(b64_data)
                except Exception:
                    image_bytes = None

                if image_bytes is None:
                    # 兼容某些网关不支持 b64_json 时，退回 URL 下载
                    image_url = image_data_item.get("url")
                    if image_url:
                        image_bytes = self.download_image(image_url)

                if not image_bytes:
                    result["error"] = f"图片下载失败 (图片 {i+1})"
                    return result

                filename = f"{filename_prefix}_{ts}_{model_suffix}_{i+1}.png"
                local_path = self.save_image(image_bytes, filename)
                image_paths.append(local_path)

            result["local_path"] = image_paths  # 返回图片路径列表
            result["success"] = True
            return result
        except Exception as e:  # noqa: BLE001
            result["error"] = str(e)
            return result


__all__ = ["ApiImageGenerator"]


