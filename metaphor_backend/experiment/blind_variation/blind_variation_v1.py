#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blind Variation 词义发散算法 (优化版)

功能：通过词向量空间扰动、语义跳跃生成异质性强的候选隐喻词
输入：一个英文名词（如 "ocean"）
输出：5个最优发散的英文名词

算法策略：
1. 自适应突变率（Adaptive Mutation Rate）
2. 语义漂移（Controlled Semantic Drift）
3. 选择压力模拟（Selection Pressure）
4. 数据事实相关性（Data Fact Relevance）

优化策略：
1. 语义不相似性过滤 - 避免同义词/复数
2. 词性过滤 - 仅保留名词
3. 多样性控制 - 确保结果间语义分散
4. 扰动幅度增强 - 增加语义漂移
"""

import numpy as np
from functools import lru_cache
import pickle
import os
from typing import List, Tuple, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')

# 尝试导入NLTK用于词性过滤
try:
    import nltk
    from nltk.corpus import wordnet as wn
    NLTK_AVAILABLE = True
    # 下载必要的NLTK数据
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    print("警告：NLTK未安装，将跳过词性过滤")

# 默认参数配置（优化版）
DEFAULT_PARAMS = {
    'beta': 10.0,      # 自适应突变率参数
    'rho_0': 0.4,      # 密度阈值
    'sigma_0': 0.12,   # 基础突变幅度（增强：0.1 -> 0.12）
    'delta': 0.6,      # 语义漂移幅度（增强：0.5 -> 0.6）
    'alpha': 0.7,      # 适应度权重（更偏重新颖性）
    'gamma': 0.2,      # 数据事实相关性权重
    'k': 20,           # k-NN邻居数
    'num_candidates': 100,  # 候选词数量（保留老参数供兼容）
    'top_k': 5,        # 返回最优词数量
    
    # 新增优化参数
    'similarity_threshold': 0.8,  # 语义不相似性过滤阈值
    'diversity_threshold': 0.7,   # 多样性控制阈值
    'min_similarity': 0.3,        # 最小相似度阈值（避免完全不相关）

    # 新算法参数
    's_min': 0.15,                 # 远域锚点相似度下限
    's_max': 0.75,                 # 远域锚点相似度上限
    'num_ring': 80,                # 环带点突变样本数
    'num_anchor': 6,               # 跨域锚点数量
    'num_segment_each': 10,        # 每个锚点的段突变样本数
    'lambda_segment': 0.6,         # 段突变强度基准（会随密度自适应）
    'ring_radius_base': 0.35,      # 环带半径基准（会随密度自适应）
    'r_side': 0.2,                 # 段突变横向扩散半径
    'mmr_lambda': 0.7,             # MMR 权衡系数
    'phrase_weight': 0.2,          # 短语评分权重 μ
    'morph_penalty_weight': 0.5,   # 形态惩罚权重 ϕ
    'nearest_k': 15,               # 回映射时最近邻数量
}

# 数据事实类别标签（用于相关性加分）
DATA_FACT_CATEGORIES = {
    'Extremum': ['peak', 'valley', 'summit', 'bottom', 'maximum', 'minimum'],
    'Distribution': ['spread', 'cluster', 'scatter', 'concentrate', 'distribute'],
    'Correlation': ['link', 'connect', 'relate', 'associate', 'correlate'],
    'Trend': ['flow', 'stream', 'current', 'direction', 'movement'],
    'Growth': ['expand', 'grow', 'increase', 'multiply', 'proliferate']
}

class BlindVariationGenerator:
    """Blind Variation 词义发散生成器（优化版）"""
    
    def __init__(self, embeddings_path: str = None, params: Dict = None):
        """
        初始化生成器
        
        Args:
            embeddings_path: 词向量文件路径
            params: 算法参数字典
        """
        self.params = {**DEFAULT_PARAMS, **(params or {})}
        self.embeddings = None
        self.word_to_idx = None
        self.idx_to_word = None
        
        self.nn_model = None
        self._noun_cache = {}

        if embeddings_path:
            self.load_embeddings(embeddings_path)
        else:
            # 优先使用.bin文件，然后是缓存文件，最后是.vec文件
            bin_path = "data/wiki-news-300d-1M.bin"
            cache_path = "data/fasttext_cache.pkl"
            vec_path = "data/wiki-news-300d-1M.vec"
            
            if os.path.exists(bin_path):
                print("发现.bin文件，优先使用...")
                self.load_embeddings(bin_path)
            elif os.path.exists(cache_path):
                print("发现缓存文件，使用缓存...")
                self.load_embeddings(cache_path)
            elif os.path.exists(vec_path):
                print("发现.vec文件，使用.vec文件...")
                self.load_embeddings(vec_path)
            else:
                # 如果没有fastText模型，使用示例词向量
                print("未发现词向量文件，使用示例词向量...")
                self._create_sample_embeddings()
    
    def load_embeddings(self, path: str) -> None:
        """
        加载词向量模型
        
        Args:
            path: 词向量文件路径（支持fastText格式或缓存文件）
        """
        print("正在加载词向量模型: {}".format(path))
        
        # 尝试加载缓存文件
        if path.endswith('.pkl'):
            self._load_from_cache(path)
        elif path.endswith('.bin') or path.endswith('.vec'):
            # fastText模型文件
            self._load_fasttext_model(path)
        else:
            # 使用示例词向量
            self._create_sample_embeddings()
        
        # 转为 float32 并统一行向量归一化，便于用点积近似余弦相似度
        if self.embeddings.dtype != np.float32:
            self.embeddings = self.embeddings.astype(np.float32)
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        print("词向量模型加载完成，词汇量: {}".format(len(self.word_to_idx)))
        # 预构建最近邻索引，避免重复fit
        try:
            self.nn_model = NearestNeighbors(metric='cosine', algorithm='brute')
            self.nn_model.fit(self.embeddings)
        except Exception as e:
            print("构建最近邻索引失败: {}".format(e))
            self.nn_model = None
    
    def _load_from_cache(self, cache_path: str) -> None:
        """从缓存文件加载词向量"""
        try:
            import pickle
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.word_to_idx = cache_data['word_to_idx']
            self.embeddings = cache_data['embeddings']
            if self.embeddings.dtype != np.float32:
                self.embeddings = self.embeddings.astype(np.float32)
            self.idx_to_word = cache_data['idx_to_word']
            
            print("成功从缓存加载词向量: {}".format(cache_path))
            
        except Exception as e:
            print("从缓存加载失败: {}".format(e))
            print("使用示例词向量")
            self._create_sample_embeddings()
    
    def _load_fasttext_model(self, model_path: str) -> None:
        """加载fastText模型"""
        try:
            from gensim.models import KeyedVectors
            
            print("正在加载fastText词向量文件: {}".format(model_path))
            
            # 根据文件扩展名选择加载方式
            if model_path.endswith('.bin'):
                # 尝试多种方式加载.bin格式文件
                word_vectors = None
                
                # 方法1: 尝试直接加载
                try:
                    word_vectors = KeyedVectors.load(model_path)
                    print("使用KeyedVectors.load()加载.bin文件")
                except:
                    # 方法2: 尝试作为word2vec格式加载
                    try:
                        word_vectors = KeyedVectors.load_word2vec_format(model_path, binary=True)
                        print("使用load_word2vec_format(binary=True)加载.bin文件")
                    except:
                        # 方法3: 尝试作为fastText格式加载
                        try:
                            word_vectors = KeyedVectors.load_word2vec_format(model_path, binary=False)
                            print("使用load_word2vec_format(binary=False)加载.bin文件")
                        except Exception as e:
                            print("所有加载方法都失败: {}".format(e))
                            raise
                
            elif model_path.endswith('.vec'):
                # 加载.vec格式文件
                word_vectors = KeyedVectors.load_word2vec_format(model_path, binary=False)
                print("使用.vec格式加载")
            else:
                raise ValueError("不支持的文件格式: {}".format(model_path))
            
            # 转换为numpy格式
            word_to_idx = {}
            embeddings = []
            idx_to_word = {}
            
            # 获取词汇列表（限制词汇量以提高性能）
            max_vocab = 50000
            vocab_list = list(word_vectors.key_to_index.keys())[:max_vocab]
            
            for idx, word in enumerate(vocab_list):
                word_to_idx[word] = idx
                vector = word_vectors[word]
                embeddings.append(vector)
                idx_to_word[idx] = word
            
            self.word_to_idx = word_to_idx
            self.embeddings = np.array(embeddings, dtype=np.float32)
            self.idx_to_word = idx_to_word
            
            print("成功加载fastText模型: {}".format(model_path))
            print("词汇量: {}, 向量维度: {}".format(len(word_to_idx), self.embeddings.shape[1]))
            
        except Exception as e:
            print("加载fastText模型失败: {}".format(e))
            print("使用示例词向量")
            self._create_sample_embeddings()
    
    def _create_sample_embeddings(self):
        """创建示例词向量（用于测试）"""
        # 示例词汇列表
        sample_words = [
            'ocean', 'sea', 'river', 'lake', 'stream', 'wave', 'tide', 'current',
            'mountain', 'hill', 'valley', 'peak', 'cliff', 'rock', 'stone',
            'forest', 'tree', 'plant', 'flower', 'grass', 'leaf',
            'fire', 'flame', 'heat', 'light', 'energy', 'power',
            'wind', 'air', 'breeze', 'storm', 'cloud', 'rain',
            'earth', 'soil', 'ground', 'land', 'field', 'desert',
            'animal', 'bird', 'fish', 'beast', 'creature',
            'human', 'person', 'people', 'crowd', 'group',
            'city', 'building', 'house', 'home', 'structure',
            'machine', 'tool', 'device', 'instrument', 'equipment'
        ]
        
        # 创建随机词向量（100维）
        np.random.seed(42)  # 确保可重现
        self.embeddings = np.random.randn(len(sample_words), 100)
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        
        # 创建词汇映射
        self.word_to_idx = {word: idx for idx, word in enumerate(sample_words)}
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
    
    def get_knn_density(self, word_vec: np.ndarray, k: int = None) -> float:
        """
        计算词向量在其局部语义空间的密度
        
        Args:
            word_vec: 输入词向量
            k: k-NN邻居数
            
        Returns:
            float: 平均邻居距离（密度指标）
        """
        k = k or self.params['k']
        
        # 使用预构建的k-NN索引
        if self.nn_model is None:
            nn = NearestNeighbors(n_neighbors=k+1, metric='cosine', algorithm='brute')
            nn.fit(self.embeddings)
            distances, indices = nn.kneighbors([word_vec])
        else:
            distances, indices = self.nn_model.kneighbors([word_vec], n_neighbors=k+1)
        
        # 排除自己，计算平均距离
        avg_distance = np.mean(distances[0][1:])
        
        return avg_distance
    
    def adaptive_mutation(self, word_vec: np.ndarray, rho: float) -> float:
        """
        自适应突变率计算
        
        Args:
            word_vec: 输入词向量
            rho: 局部密度
            
        Returns:
            float: 突变幅度
        """
        beta = self.params['beta']
        rho_0 = self.params['rho_0']
        sigma_0 = self.params['sigma_0']
        
        # 计算自适应函数
        f_rho = 1 / (1 + np.exp(-beta * (rho - rho_0)))
        
        # 计算突变幅度
        sigma = sigma_0 * f_rho
        
        return sigma
    
    def semantic_drift(self, word_vec: np.ndarray, delta: float = None, num: int = None) -> List[np.ndarray]:
        """
        语义漂移：在与主题词向量正交的方向上生成多个单位向量
        
        Args:
            word_vec: 原始词向量
            delta: 漂移幅度
            num: 生成候选数量
            
        Returns:
            List[np.ndarray]: 漂移后的候选词向量列表
        """
        delta = delta or self.params['delta']
        num = num or self.params['num_candidates']
        
        candidates = []
        
        for _ in range(num):
            # 生成随机向量
            random_vec = np.random.randn(word_vec.shape[0])
            
            # 归一化
            random_vec = random_vec / np.linalg.norm(random_vec)
            
            # 计算与原始向量的正交分量
            projection = np.dot(random_vec, word_vec) * word_vec
            orthogonal_vec = random_vec - projection
            
            # 归一化正交向量
            if np.linalg.norm(orthogonal_vec) > 1e-8:
                orthogonal_vec = orthogonal_vec / np.linalg.norm(orthogonal_vec)
            else:
                # 如果正交向量太小，使用随机向量
                orthogonal_vec = random_vec
            
            # 应用漂移
            drifted_vec = word_vec + delta * orthogonal_vec
            
            # 归一化结果
            drifted_vec = drifted_vec / np.linalg.norm(drifted_vec)
            
            candidates.append(drifted_vec)
        
        return candidates
    
    def compute_fitness(self, v_prime: np.ndarray, v_orig: np.ndarray, 
                       v_theme: np.ndarray = None, alpha: float = None) -> float:
        """
        计算适应度分数
        
        Args:
            v_prime: 候选词向量
            v_orig: 原始词向量
            v_theme: 主题词向量（可选）
            alpha: 新颖性权重
            
        Returns:
            float: 适应度分数
        """
        alpha = alpha or self.params['alpha']
        
        # 计算新颖性（与原始向量的差异）
        novelty = 1 - cosine_similarity([v_prime], [v_orig])[0][0]
        
        # 计算相关性（与主题向量的相似度）
        if v_theme is not None:
            relevance = cosine_similarity([v_prime], [v_theme])[0][0]
        else:
            # 如果没有主题向量，使用与原始向量的相关性
            relevance = cosine_similarity([v_prime], [v_orig])[0][0]
        
        # 计算适应度
        fitness = alpha * novelty + (1 - alpha) * relevance
        
        return fitness
    
    def get_data_fact_score(self, word: str) -> float:
        """
        计算数据事实相关性分数
        
        Args:
            word: 候选词
            
        Returns:
            float: 相关性分数
        """
        word_lower = word.lower()
        
        for category, related_words in DATA_FACT_CATEGORIES.items():
            if word_lower in [w.lower() for w in related_words]:
                return 1.0
        
        return 0.0

    def _data_fact_score_token(self, token: str) -> float:
        # 若是短语，取最后一个词作为head进行打分
        if ' ' in token:
            head = token.split()[-1]
            return self.get_data_fact_score(head)
        return self.get_data_fact_score(token)
    
    def find_nearest_words(self, vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        找到与给定向量最相似的词
        
        Args:
            vector: 目标向量
            top_k: 返回前k个最相似的词
            
        Returns:
            List[Tuple[str, float]]: (词, 相似度) 列表
        """
        # 优先用k-NN索引快速筛选，再精排
        if self.nn_model is not None and top_k <= 100:
            # 先取更大的候选集合再排序
            k_probe = min(len(self.idx_to_word), max(5*top_k, top_k))
            distances, indices = self.nn_model.kneighbors([vector], n_neighbors=k_probe)
            indices = indices[0]
            sims_subset = 1.0 - distances[0]
            pairs = [(int(i), float(s)) for i, s in zip(indices, sims_subset)]
            pairs.sort(key=lambda x: x[1], reverse=True)
            pairs = pairs[:top_k]
            return [(self.idx_to_word[i], s) for i, s in pairs]
        else:
            # 回退到全量相似度（较慢）
            similarities = cosine_similarity([vector], self.embeddings)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            return [(self.idx_to_word[int(idx)], float(similarities[int(idx)])) for idx in top_indices]

    # ===================== 新算法辅助函数 =====================
    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec)
        if norm < 1e-12:
            return vec
        return vec / norm

    def _random_unit_orthogonal(self, ref_vec: np.ndarray) -> np.ndarray:
        rand = np.random.randn(ref_vec.shape[0])
        rand = self._normalize(rand)
        proj = np.dot(rand, ref_vec) * ref_vec
        ortho = rand - proj
        if np.linalg.norm(ortho) < 1e-8:
            # 退化时重新采样
            rand = np.random.randn(ref_vec.shape[0])
            rand = self._normalize(rand)
            proj = np.dot(rand, ref_vec) * ref_vec
            ortho = rand - proj
        return self._normalize(ortho)

    def _morphologically_similar(self, a: str, b: str) -> bool:
        a_l = a.lower(); b_l = b.lower()
        if a_l == b_l:
            return True
        # 简单词形判断：复数/常见派生
        def stem_endings(x):
            pairs = [
                ('ies', 'y'), ('es', ''), ('s', ''),
                ('ing', ''), ('ed', ''), ('er', ''), ('est', ''),
            ]
            stems = set([x])
            for suf, rep in pairs:
                if x.endswith(suf) and len(x) > len(suf) + 1:
                    stems.add(x[:-len(suf)] + rep)
            return stems
        return len(stem_endings(a_l).intersection(stem_endings(b_l))) > 0

    def _dedup_preserve_order(self, tokens: List[str]) -> List[str]:
        seen = set()
        out = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out

    def _mmr_select(self, items: List[Tuple[str, float, np.ndarray]], top_k: int, mmr_lambda: float) -> List[Tuple[str, float, np.ndarray]]:
        # items: (token, fitness, vector)
        if len(items) <= top_k:
            return items
        selected = []
        remaining = items[:]
        # 先选当前fitness最高的
        remaining.sort(key=lambda x: x[1], reverse=True)
        selected.append(remaining.pop(0))
        while len(selected) < top_k and remaining:
            best_idx = 0
            best_score = -1e9
            for i, (tok, fit, vec) in enumerate(remaining):
                # 与已选集合的最大相似度
                max_sim = 0.0
                for _, _, svec in selected:
                    sim = cosine_similarity([vec], [svec])[0][0]
                    if sim > max_sim:
                        max_sim = sim
                score = mmr_lambda * fit - (1 - mmr_lambda) * max_sim
                if score > best_score:
                    best_score = score
                    best_idx = i
            selected.append(remaining.pop(best_idx))
        return selected

    def _discover_cross_domain_anchors(self, v0: np.ndarray, s_min: float, s_max: float, num_anchor: int) -> List[np.ndarray]:
        sims = cosine_similarity([v0], self.embeddings)[0]
        candidates = []
        for idx, sim in enumerate(sims):
            if s_min <= sim <= s_max:
                candidates.append((idx, sim))
        if not candidates:
            # 回退：取相似度最低的若干个
            order = np.argsort(sims)[:max(1, num_anchor*3)]
            candidates = [(int(i), float(sims[int(i)])) for i in order]
        # 最远点采样，覆盖不同区域
        chosen = []
        if not candidates:
            return chosen
        # 先取相似度位于中间的一个作为起点
        candidates.sort(key=lambda x: x[1])
        start_idx = candidates[len(candidates)//2][0]
        chosen.append(start_idx)
        while len(chosen) < min(num_anchor, len(candidates)):
            best_i = None
            best_d = -1
            for idx, _ in candidates:
                if idx in chosen:
                    continue
                vec = self.embeddings[idx]
                # 距已选集合的最小距离最大化
                min_d = 1e9
                for c in chosen:
                    d = 1 - cosine_similarity([vec], [self.embeddings[c]])[0][0]
                    if d < min_d:
                        min_d = d
                if min_d > best_d:
                    best_d = min_d
                    best_i = idx
            if best_i is None:
                break
            chosen.append(best_i)
        return [self.embeddings[i] for i in chosen]

    def _make_phrases(self, input_word: str, base_tokens: List[str], anchor_tokens: List[str]) -> List[str]:
        phrases = []
        # 仅在均为名词时组成短语
        for a in anchor_tokens:
            if not self.is_noun(a):
                continue
            # anchor + input 或 input + anchor
            if self.is_noun(input_word):
                phrases.append("{} {}".format(a, input_word))
                phrases.append("{} {}".format(input_word, a))
        # 也可用部分邻近名词作为修饰词
        for b in base_tokens[:3]:
            if b.lower() == input_word.lower():
                continue
            if self.is_noun(b) and self.is_noun(input_word):
                phrases.append("{} {}".format(b, input_word))
                phrases.append("{} {}".format(input_word, b))
        return self._dedup_preserve_order(phrases)

    def _phrase_score(self, phrase: str) -> float:
        # 简化：名词-名词短语给定一个小的正分
        parts = phrase.split()
        if len(parts) != 2:
            return 0.0
        if self.is_noun(parts[0]) and self.is_noun(parts[1]):
            return 1.0
        return 0.0
    
    def is_noun(self, word: str) -> bool:
        """
        策略2：词性过滤 - 检查词是否为名词
        
        Args:
            word: 待检查的词
            
        Returns:
            bool: 是否为名词
        """
        # 简单缓存，降低重复计算成本
        wl = word.lower()
        if wl in self._noun_cache:
            return self._noun_cache[wl]

        if not NLTK_AVAILABLE:
            # 如果NLTK不可用，使用简单的启发式规则
            res = self._heuristic_noun_check(word)
            self._noun_cache[wl] = res
            return res
        
        try:
            # 使用WordNet检查词性
            synsets = wn.synsets(word, pos=wn.NOUN)
            res = len(synsets) > 0
            self._noun_cache[wl] = res
            return res
        except:
            # 如果WordNet检查失败，使用启发式规则
            res = self._heuristic_noun_check(word)
            self._noun_cache[wl] = res
            return res
    
    def _heuristic_noun_check(self, word: str) -> bool:
        """
        启发式名词检查（当NLTK不可用时使用）
        
        Args:
            word: 待检查的词
            
        Returns:
            bool: 是否为名词
        """
        # 简单的启发式规则
        word_lower = word.lower()
        
        # 排除常见的非名词后缀
        non_noun_suffixes = ['ing', 'ed', 'ly', 'ful', 'less', 'able', 'ible', 'ous', 'al', 'ic']
        for suffix in non_noun_suffixes:
            if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 2:
                return False
        
        # 排除常见的动词/形容词
        non_nouns = {'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 
                    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can',
                    'very', 'much', 'many', 'few', 'little', 'big', 'small', 'good', 'bad'}
        
        return word_lower not in non_nouns
    
    def filter_semantic_similarity(self, candidates: List[Tuple[str, float, float]], 
                                 original_word: str, original_vec: np.ndarray) -> List[Tuple[str, float, float]]:
        """
        策略1：语义不相似性过滤 - 过滤掉与原始词过于相似的候选词
        
        Args:
            candidates: 候选词列表 [(word, fitness, similarity), ...]
            original_word: 原始词
            original_vec: 原始词向量
            
        Returns:
            List[Tuple[str, float, float]]: 过滤后的候选词列表
        """
        threshold = self.params['similarity_threshold']
        min_sim = self.params['min_similarity']
        filtered = []
        
        for word, fitness, similarity in candidates:
            # 跳过与原始词相同的词
            if word.lower() == original_word.lower():
                continue
            
            # 计算与原始词的相似度
            if word in self.word_to_idx:
                word_vec = self.embeddings[self.word_to_idx[word]]
                sim_to_original = cosine_similarity([word_vec], [original_vec])[0][0]
                
                # 过滤条件：相似度在合理范围内
                if min_sim <= sim_to_original <= threshold:
                    filtered.append((word, fitness, similarity))
        
        return filtered
    
    def filter_by_pos(self, candidates: List[Tuple[str, float, float]]) -> List[Tuple[str, float, float]]:
        """
        策略2：词性过滤 - 仅保留名词
        
        Args:
            candidates: 候选词列表 [(word, fitness, similarity), ...]
            
        Returns:
            List[Tuple[str, float, float]]: 过滤后的候选词列表
        """
        filtered = []
        for word, fitness, similarity in candidates:
            if self.is_noun(word):
                filtered.append((word, fitness, similarity))
        
        return filtered
    
    def ensure_diversity(self, candidates: List[Tuple[str, float, float]], 
                        top_k: int = 5) -> List[Tuple[str, float, float]]:
        """
        策略3：多样性控制 - 确保结果间的语义多样性
        
        Args:
            candidates: 候选词列表 [(word, fitness, similarity), ...]
            top_k: 返回的候选词数量
            
        Returns:
            List[Tuple[str, float, float]]: 多样化的候选词列表
        """
        if len(candidates) <= top_k:
            return candidates[:top_k]
        
        # 按适应度排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        threshold = self.params['diversity_threshold']
        
        for word, fitness, similarity in candidates:
            # 检查与已选择词的相似度
            is_diverse = True
            
            for selected_word, _, _ in selected:
                if word in self.word_to_idx and selected_word in self.word_to_idx:
                    word_vec = self.embeddings[self.word_to_idx[word]]
                    selected_vec = self.embeddings[self.word_to_idx[selected_word]]
                    sim = cosine_similarity([word_vec], [selected_vec])[0][0]
                    
                    if sim > threshold:
                        is_diverse = False
                        break
            
            if is_diverse:
                selected.append((word, fitness, similarity))
                
                if len(selected) >= top_k:
                    break
        
        # 如果多样性过滤后数量不足，补充剩余的高适应度词
        if len(selected) < top_k:
            remaining = [c for c in candidates if c[0] not in [s[0] for s in selected]]
            selected.extend(remaining[:top_k - len(selected)])
        
        return selected[:top_k]
    
    def blind_variation_generate(self, input_word: str) -> List[Tuple[str, float]]:
        """
        新算法：环带点突变 + 锚点段突变 + 短语重组 + MMR多样化
        """
        lw = input_word.lower()
        if lw not in self.word_to_idx:
            print("警告：词汇 '{}' 不在词向量模型中".format(input_word))
            return []

        v0 = self.embeddings[self.word_to_idx[lw]]
        print("处理输入词: {}".format(input_word))

        # 局部密度与自适应幅度
        rho = self.get_knn_density(v0)
        print("局部密度 (rho): {:.4f}".format(rho))
        sigma = self.adaptive_mutation(v0, rho)
        print("自适应突变率 (sigma): {:.4f}".format(sigma))

        # 自适应环带半径与段突变强度
        ring_radius = self.params['ring_radius_base'] + 0.5 * sigma
        lam_seg = self.params['lambda_segment'] * (1.0 + sigma)
        r_side = self.params['r_side']

        # 发现跨域锚点
        anchors = self._discover_cross_domain_anchors(
            v0,
            self.params['s_min'],
            self.params['s_max'],
            self.params['num_anchor']
        )

        # 生成候选（环带点突变）
        candidate_vecs = []
        for _ in range(self.params['num_ring']):
            u = self._random_unit_orthogonal(v0)
            v = self._normalize(v0 + ring_radius * u)
            candidate_vecs.append(v)

        # 生成候选（锚点段突变）
        for a in anchors:
            d = self._normalize(a - v0)
            for _ in range(self.params['num_segment_each']):
                eta = self._random_unit_orthogonal(d)
                v = self._normalize(v0 + lam_seg * d + r_side * eta)
                candidate_vecs.append(v)

        print("生成候选向量数: {}".format(len(candidate_vecs)))

        # 准备锚点token用于短语重组
        anchor_tokens = []
        for a in anchors:
            near_a = self.find_nearest_words(a, top_k=1)
            if near_a:
                if self.is_noun(near_a[0][0]):
                    anchor_tokens.append(near_a[0][0])
        anchor_tokens = self._dedup_preserve_order(anchor_tokens)

        # 候选映射与打分
        scored = []
        min_sim = self.params['min_similarity']
        max_sim = self.params['similarity_threshold']
        nearest_k = self.params['nearest_k']
        alpha = self.params['alpha']
        gamma = self.params['gamma']
        mu = self.params['phrase_weight']
        phi = self.params['morph_penalty_weight']

        # 预计算与 v0 的相似度（批量）
        if len(candidate_vecs) == 0:
            print("无候选向量")
            return []
        c_mat = np.vstack(candidate_vecs)
        sim0_vec = cosine_similarity(c_mat, v0.reshape(1, -1))[:, 0]

        for v, sim0 in zip(candidate_vecs, sim0_vec):
            sim0 = float(sim0)
            # 限制与原词的相似度窗口，避免过近或完全无关
            if not (min_sim <= sim0 <= max_sim):
                continue

            # 近邻名词
            near = self.find_nearest_words(v, top_k=nearest_k)
            base_tokens = [w for (w, s) in near if self.is_noun(w) and w.lower() != lw]
            base_tokens = [w for w in base_tokens if not self._morphologically_similar(w, input_word)]
            base_tokens = self._dedup_preserve_order(base_tokens)

            # 短语重组
            phrase_tokens = self._make_phrases(input_word, base_tokens, anchor_tokens)

            # 汇总候选token（词 + 短语）
            candidate_tokens = base_tokens[:5] + phrase_tokens[:5]

            for token in candidate_tokens:
                # 词性/短语合法性
                if ' ' in token:
                    if self._phrase_score(token) <= 0.0:
                        continue
                else:
                    if not self.is_noun(token):
                        continue

                novelty = 1.0 - sim0
                relevance = sim0
                data_score = self._data_fact_score_token(token)
                phrase_score = self._phrase_score(token)
                morph_penalty = 1.0 if self._morphologically_similar(token.split()[-1], input_word) else 0.0
                fitness = alpha * novelty + (1.0 - alpha) * relevance + gamma * data_score + mu * phrase_score - phi * morph_penalty
                scored.append((token, float(fitness), v))

        if not scored:
            print("无有效候选，返回空结果")
            return []

        # MMR 多样化选择
        mmr_lambda = self.params['mmr_lambda']
        top_k = self.params['top_k']
        selected = self._mmr_select(scored, top_k, mmr_lambda)
        print("MMR 选择后候选词数量: {}".format(len(selected)))

        # 输出 (token, fitness)
        final_results = [(tok, fit) for (tok, fit, _) in selected]
        return final_results


def main():
    """主函数：测试Blind Variation算法（优化版）"""
    print("=== Blind Variation 词义发散算法测试（优化版）===\n")
    
    # 创建生成器实例
    generator = BlindVariationGenerator()
    
    # 测试词汇列表
    test_words = ["ocean", "mountain", "fire", "wind", "city"]
    
    for test_word in test_words:
        print("\n" + "=" * 50)
        print("测试输入词: {}".format(test_word))
        print("=" * 50)
        
        # 生成发散词汇
        results = generator.blind_variation_generate(test_word)
        
        if results:
            print("\n最优发散词汇（前{}个）:".format(len(results)))
            print("-" * 40)
            for i, (word, fitness) in enumerate(results, 1):
                print("{:2d}. {:15s} (适应度: {:.4f})".format(i, word, fitness))
        else:
            print("未找到合适的发散词汇")
        
        print()


if __name__ == "__main__":
    main() 