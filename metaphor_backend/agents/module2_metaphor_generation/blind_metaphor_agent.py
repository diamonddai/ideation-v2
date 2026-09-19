import sys
import os
from pathlib import Path

# 添加experiment路径到sys.path
experiment_path = Path(__file__).parent.parent.parent / "experiment" / "blind_variation"
sys.path.append(str(experiment_path))

from pydantic import BaseModel
from fastapi import APIRouter
from typing import List, Dict, Any, Optional
import os
import json
import logging

# 导入常量
from .constants import BLIND

# 可选：LLM 支持作为兜底
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

# 导入V4算法
try:
    from blind_variation_v4 import OptimizedBlindVariation
    V4_AVAILABLE = True
except ImportError as e:
    logging.warning(f"V4算法导入失败: {e}")
    V4_AVAILABLE = False

router = APIRouter()

class BoundField(BaseModel):
    field: str
    dataFact: str

class MetaphorVariation(BaseModel):
    field: str
    keyword: str
    dataFact: str
    method: int = BLIND
    score: Optional[float] = None  # 添加分数字段

class BlindVariationInput(BaseModel):
    boundField: BoundField

class BlindVariationOutput(BaseModel):
    variations: List[MetaphorVariation]

class SimpleBlindItem(BaseModel):
    field: str
    keyword: str
    dataFact: str

# 全局V4生成器实例
_v4_generator = None

def get_v4_generator():
    """获取V4生成器实例（单例模式）"""
    global _v4_generator
    if _v4_generator is None and V4_AVAILABLE:
        try:
            # 设置工作目录到experiment/blind_variation
            original_cwd = os.getcwd()
            os.chdir(str(experiment_path))
            
            # 创建生成器实例
            _v4_generator = OptimizedBlindVariation()
            
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
            logging.info("V4生成器初始化成功")
        except Exception as e:
            logging.error(f"V4生成器初始化失败: {e}")
            _v4_generator = None
    
    return _v4_generator

def is_valid_keyword(keyword: str) -> bool:
    """检查关键词是否有效"""
    if not keyword or len(keyword) < 2:
        return False
    
    # 过滤掉包含特殊字符的结果
    if any(char in keyword for char in ["'", '"', "\\", "/", "|", "&", "=", "+", "*", "(", ")", "[", "]", "{", "}"]):
        return False
    
    # 过滤掉纯数字
    if keyword.isdigit():
        return False
    
    # 过滤掉过短的词
    if len(keyword) < 3:
        return False
    
    return True

def _is_technical_term(keyword: str) -> bool:
    """检查是否为技术术语或文件后缀"""
    keyword_lower = keyword.lower()
    
    # 文件后缀
    file_extensions = {
        'json', 'xml', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c', 'h',
        'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'jpg', 'jpeg', 'png', 'gif', 'svg', 'mp4', 'avi', 'mp3', 'wav',
        'zip', 'rar', 'tar', 'gz', 'exe', 'dll', 'so', 'dylib'
    }
    
    if keyword_lower in file_extensions:
        return True
    
    # 技术术语
    tech_terms = {
        'api', 'url', 'http', 'https', 'sql', 'mysql', 'redis', 'mongodb',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'rest', 'graphql',
        'oauth', 'jwt', 'ssl', 'tls', 'cors', 'csrf', 'xss', 'csrf',
        'json', 'yaml', 'xml', 'csv', 'tsv', 'log', 'config', 'env',
        'git', 'github', 'gitlab', 'bitbucket', 'npm', 'yarn', 'pip',
        'node', 'react', 'vue', 'angular', 'django', 'flask', 'spring',
        # 编程语言内置函数和关键字
        'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set', 'range',
        'print', 'input', 'open', 'close', 'read', 'write', 'append', 'remove', 'pop',
        'split', 'join', 'replace', 'strip', 'lower', 'upper', 'title', 'capitalize',
        'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'import', 'from', 'return',
        'try', 'except', 'finally', 'with', 'as', 'in', 'is', 'and', 'or', 'not',
        'true', 'false', 'null', 'none', 'self', 'super', 'init', 'new', 'this'
    }
    
    if keyword_lower in tech_terms:
        return True
    
    return False

async def blind_variation_agent(input_data: BlindVariationInput) -> BlindVariationOutput:
    """
    Blind 语义扰动发散 Agent：
    - 作用：通过词向量空间扰动、语义跳跃生成异质性强的候选隐喻
    - 输入：绑定字段（field + dataFact）
    - 输出：多个隐喻变体，保持 dataFact 不变
    - 算法：三层向量漂移突变机制（V4优化版）
    """
    try:
        field = input_data.boundField.field
        data_fact = input_data.boundField.dataFact
        
        logging.info(f"开始Blind Variation生成 - field: {field}, dataFact: {data_fact}")
        
        # 获取V4生成器
        generator = get_v4_generator()
        
        if generator is None:
            logging.warning("V4生成器不可用，使用默认示例数据")
            # 回退到默认示例数据
            default_variations = [
                MetaphorVariation(field=field, keyword="flood", dataFact=data_fact, method=BLIND, score=0.8),
                MetaphorVariation(field=field, keyword="explosion", dataFact=data_fact, method=BLIND, score=0.7),
                MetaphorVariation(field=field, keyword="avalanche", dataFact=data_fact, method=BLIND, score=0.6)
            ]
            return BlindVariationOutput(variations=default_variations)
        
        # 使用V4算法生成发散词汇
        input_word = field
        
        # 调用V4算法
        results = generator.blind_variation_generate(input_word)
        if not results:
            # 兜底策略1：LLM 生成（默认开启，可用 BLIND_LLM_FALLBACK 关闭）
            use_llm_fallback = os.getenv("BLIND_LLM_FALLBACK", "true").lower() in ["1", "true", "yes"]
            if use_llm_fallback and LLM_AVAILABLE:
                try:
                    llm = ChatOpenAI(
                        model=os.getenv("BLIND_LLM_MODEL", "gpt-4o-mini"),
                        temperature=0.6,
                        openai_api_key=os.getenv("OPENAI_API_KEY"),
                        openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.nbai.art/v1")
                    )
                    sys_prompt = (
                        "你是一个名词发散助手。根据输入的 field 和 dataFact，给出5-10个英文单词，"
                        "每个必须是可用作隐喻的普通名词（避免专有名词/复数/动词/形容词），避免与原词形态相似。"
                        "只返回 JSON 数组，例如: [\"wave\", \"tide\", ...]。"
                    )
                    user_prompt = (
                        f"field: {field}\n"
                        f"dataFact: {data_fact}\n"
                        "要求：1) 单词小写; 2) 避免复数; 3) 与 field 不为同形或词形变化; 4) 语义尽量多样。"
                    )
                    messages = [SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)]
                    resp = llm.invoke(messages)
                    text = (resp.content or "").strip()
                    candidates = []
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, list):
                            candidates = [str(x) for x in parsed if isinstance(x, str)]
                    except Exception:
                        import re
                        candidates = re.findall(r"[A-Za-z][a-z]{2,}", text)
                    dedup = []
                    seen = set()
                    field_l = field.lower()
                    for w in candidates:
                        wl = w.lower()
                        if wl in seen:
                            continue
                        if len(wl) < 3 or len(wl) > 12:
                            continue
                        if wl.endswith('s'):
                            continue
                        if wl == field_l or wl.rstrip('s') == field_l.rstrip('s'):
                            continue
                        # ✅ 添加技术术语过滤
                        if _is_technical_term(wl):
                            continue
                        seen.add(wl)
                        dedup.append((wl, 0.55))
                    if dedup:
                        results = dedup
                        print(f"🔁 Blind 使用 LLM 兜底生成 {len(dedup)} 个候选：{[w for w,_ in dedup]}")
                except Exception as e:
                    print(f"⚠️ Blind LLM 兜底失败: {e}")

            # 兜底策略2：静态大集合（最终保障，减少重复概率）
            if not results:
                static_words = [
                    "wave","tide","storm","bridge","forest","galaxy","reef","volcano","desert","oasis",
                    "compass","mirror","labyrinth","canvas","symphony","beacon","harbor","river","avalanche","furnace",
                    "nebula","aurora","meadow","archipelago","crystal","engine","palette","prism","mosaic","vine",
                    "seed","meteor","orbit","quarry","forge","anchor","lantern","spring","delta","horizon",
                    "island","canyon","harvest","lighthouse","corridor","cathedral","tunnel","fountain","glacier"
                ]
                # 去重并赋默认分数
                seen_sw = set()
                fallback_candidates = []
                for w in static_words:
                    wl = w.lower()
                    if wl in seen_sw:
                        continue
                    seen_sw.add(wl)
                    fallback_candidates.append((wl, 0.52))
                results = fallback_candidates
                print(f"🔁 Blind 使用静态兜底，共 {len(fallback_candidates)} 个候选")
        
        # 转换为输出格式，过滤低质量结果
        variations = []
        for keyword, score in results:
            # 过滤低质量结果
            if is_valid_keyword(keyword):
                # 额外过滤：排除明显的技术术语和文件后缀
                if not _is_technical_term(keyword):
                    variation = MetaphorVariation(
                        field=field,
                        keyword=keyword,
                        dataFact=data_fact,
                        method=BLIND,
                        score=score
                    )
                    variations.append(variation)
                else:
                    logging.info(f"BlindV4 technical term filtered: '{keyword}'")
        
        # 如果过滤后结果太少，使用兜底策略
        if len(variations) < 3:
            logging.warning(f"BlindV4 filtered results too few ({len(variations)}), using fallback")
            fallback_keywords = ["ocean", "mountain", "fire", "wind", "forest", "river"]
            for keyword in fallback_keywords:
                if keyword not in [v.keyword for v in variations]:
                    variations.append(MetaphorVariation(
                        field=field,
                        keyword=keyword,
                        dataFact=data_fact,
                        method=BLIND,
                        score=0.5
                    ))
                    if len(variations) >= 3:
                        break
        
        logging.info(f"Blind Variation生成完成，共生成 {len(variations)} 个变体")
        
        return BlindVariationOutput(variations=variations)
        
    except Exception as e:
        logging.error(f"Blind Variation生成失败: {e}")
        # 错误处理：返回空结果
        return BlindVariationOutput(variations=[])

# HTTP 路由：/generate/blind 返回简化数组格式
@router.post("/generate/blind", response_model=List[SimpleBlindItem])
async def blind_variation_http(input_data: BlindVariationInput) -> List[SimpleBlindItem]:
    try:
        core = await blind_variation_agent(input_data)
        simplified: List[SimpleBlindItem] = [
            SimpleBlindItem(field=v.field, keyword=v.keyword, dataFact=v.dataFact)
            for v in core.variations
        ]
        return simplified
    except Exception:
        return []

 