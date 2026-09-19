#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blind Variation 词义发散算法 - V4（优化版）

优化目标：
1. 计算时间控制在30秒以内
2. 提高结果质量，避免同义词和词形变化
3. 更好的生物启发策略实现
"""

import os
import pickle
import re
import time
import logging
from typing import Dict, List, Tuple, Any, Set
from collections import defaultdict

import numpy as np
from scipy.spatial.distance import cosine

# NLTK 支持
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk.tag import pos_tag
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    wn = None

# 词频过滤支持
try:
    from wordfreq import zipf_frequency
    WORDFREQ_AVAILABLE = True
except ImportError:
    WORDFREQ_AVAILABLE = False
    zipf_frequency = None


class OptimizedBlindVariation:
    """优化版Blind Variation算法"""
    
    def __init__(self, embeddings_path=None, params=None):
        # 默认参数配置
        self.default_params = {
            # 基因突变策略参数
            'mutation_rates': [0.2, 0.5, 0.8],  # 小、中、大幅突变率
            'mutation_weights': [0.3, 0.4, 0.3],  # 各突变类型的权重
            
            # 生态位探索参数
            'niche_radius': 0.6,  # 生态位搜索半径
            'sparsity_threshold': 0.3,  # 稀疏度阈值
            
            # 适应性辐射参数
            'radiation_directions': 8,  # 辐射方向数
            'radiation_strength': 0.7,  # 辐射强度
            'diversity_threshold': 0.7,  # 多样性阈值
            
            # 通用参数
            'top_k': 5,  # 返回结果数
            'min_zipf': 4.5,  # 最小词频阈值
            'max_similarity': 0.8,  # 最大相似度阈值
            'min_similarity': 0.1,  # 最小相似度阈值
            'min_results': 3,       # 最少返回结果
            'max_fallback_depth': 1 # 二级发散最大深度
        }
        
        self.params = self.default_params.copy()
        if params:
            self.params.update(params)
            
        # 初始化词向量模型
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.embeddings = None
        self.word_frequencies = {}
        
        # 加载词向量
        if embeddings_path:
            self.load_embeddings(embeddings_path)
        else:
            self.load_default_embeddings()
            
        # 预计算语义空间特征
        self._precompute_semantic_features()
        
    def load_embeddings(self, path):
        """加载词向量模型"""
        print(f"正在加载词向量模型: {path}")
        
        if path.endswith('.pkl'):
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.word_to_idx = data['word_to_idx']
            self.embeddings = data['embeddings'].astype(np.float32)
            self.idx_to_word = data['idx_to_word']
        else:
            raise ValueError(f"不支持的文件格式: {path}")
            
        # 标准化向量
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
        self.embeddings = self.embeddings / norms
        
        print(f"词向量模型加载完成，词汇量: {len(self.word_to_idx)}")
        
    def load_default_embeddings(self):
        """加载默认词向量"""
        cache_path = "data/fasttext_cache.pkl"
        if os.path.exists(cache_path):
            print(f"✓ 发现缓存文件: {cache_path}")
            self.load_embeddings(cache_path)
        else:
            print("⚠ 未发现缓存文件，使用示例词向量")
            self._create_sample_embeddings()
            
    def _create_sample_embeddings(self):
        """创建示例词向量"""
        print("📝 正在创建示例词向量...")
        words = [
            'ocean', 'sea', 'river', 'lake', 'wave', 'current', 'tide', 'shore', 'reef',
            'mountain', 'peak', 'valley', 'cliff', 'rock', 'stone', 'ridge',
            'city', 'town', 'village', 'street', 'bridge', 'harbor',
            'computer', 'device', 'machine', 'engine', 'network', 'data', 'analysis', 'model',
            'fire', 'flame', 'heat', 'light', 'energy', 'spark', 'blaze',
            'wind', 'storm', 'breeze', 'cloud', 'rain', 'thunder', 'lightning',
            'tree', 'forest', 'plant', 'flower', 'grass', 'leaf', 'root',
            'animal', 'bird', 'fish', 'mammal', 'reptile', 'insect',
            'book', 'story', 'poem', 'novel', 'article', 'text',
            'music', 'song', 'melody', 'rhythm', 'harmony', 'sound',
            'art', 'painting', 'sculpture', 'design', 'color', 'shape',
            'science', 'research', 'experiment', 'theory', 'discovery',
            'business', 'company', 'market', 'trade', 'commerce', 'industry',
            'education', 'school', 'university', 'learning', 'knowledge', 'wisdom',
            'family', 'home', 'house', 'room', 'kitchen', 'garden',
            'food', 'meal', 'dish', 'recipe', 'cooking', 'taste',
            'time', 'clock', 'hour', 'minute', 'second', 'moment',
            'space', 'universe', 'planet', 'star', 'galaxy', 'cosmos',
            'mind', 'thought', 'idea', 'concept', 'memory', 'dream',
            'body', 'heart', 'brain', 'muscle', 'bone', 'blood',
            'language', 'word', 'sentence', 'speech', 'voice', 'sound',
            'number', 'count', 'measure', 'size', 'amount', 'quantity',
            'path', 'road', 'way', 'direction', 'journey', 'travel',
            'tool', 'instrument', 'device', 'machine', 'equipment', 'apparatus',
            'material', 'substance', 'element', 'compound', 'molecule', 'atom',
            'pattern', 'structure', 'form', 'shape', 'design', 'arrangement',
            'system', 'network', 'web', 'connection', 'link', 'relation',
            'process', 'method', 'technique', 'procedure', 'approach', 'strategy',
            'result', 'outcome', 'effect', 'consequence', 'impact', 'influence',
            'change', 'transformation', 'evolution', 'development', 'growth', 'progress',
            'problem', 'challenge', 'difficulty', 'obstacle', 'barrier', 'hurdle',
            'solution', 'answer', 'resolution', 'fix', 'repair', 'cure',
            'success', 'achievement', 'victory', 'triumph', 'accomplishment', 'win',
            'failure', 'defeat', 'loss', 'mistake', 'error', 'fault',
            'love', 'hate', 'fear', 'joy', 'sadness', 'anger',
            'friend', 'enemy', 'stranger', 'neighbor', 'colleague', 'partner',
            'leader', 'follower', 'teacher', 'student', 'master', 'apprentice',
            'hero', 'villain', 'warrior', 'soldier', 'guard', 'protector',
            'king', 'queen', 'prince', 'princess', 'noble', 'commoner',
            'god', 'goddess', 'angel', 'demon', 'spirit', 'ghost',
            'heaven', 'hell', 'paradise', 'purgatory', 'afterlife', 'soul',
            'life', 'death', 'birth', 'rebirth', 'existence', 'being',
            'truth', 'lie', 'fact', 'fiction', 'reality', 'fantasy',
            'beauty', 'ugliness', 'grace', 'elegance', 'charm', 'attraction',
            'strength', 'weakness', 'power', 'force', 'energy', 'might',
            'speed', 'velocity', 'acceleration', 'motion', 'movement', 'action',
            'weight', 'mass', 'gravity', 'density', 'volume', 'capacity',
            'temperature', 'heat', 'cold', 'warmth', 'chill', 'freeze',
            'light', 'darkness', 'shadow', 'brightness', 'glow', 'shine',
            'color', 'hue', 'tint', 'shade', 'tone', 'pigment',
            'sound', 'noise', 'silence', 'echo', 'resonance', 'vibration',
            'smell', 'odor', 'fragrance', 'scent', 'aroma', 'perfume',
            'taste', 'flavor', 'sweetness', 'bitterness', 'sourness', 'saltiness',
            'touch', 'texture', 'smoothness', 'roughness', 'softness', 'hardness'
        ]
        
        np.random.seed(42)
        dim = 300
        E = np.random.randn(len(words), dim).astype(np.float32)
        E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-12)
        
        self.embeddings = E
        self.word_to_idx = {w: i for i, w in enumerate(words)}
        self.idx_to_word = {i: w for w, i in self.word_to_idx.items()}
        print("✅ 示例词向量创建完成（{} 词, {} 维）".format(len(words), dim))
        
    def _precompute_semantic_features(self):
        """预计算语义空间特征"""
        print("预计算语义空间特征...")
        
        # 计算词频信息
        if WORDFREQ_AVAILABLE:
            for word in self.word_to_idx:
                try:
                    freq = zipf_frequency(word, 'en')
                    self.word_frequencies[word] = freq
                except:
                    self.word_frequencies[word] = 5.0
        else:
            for word in self.word_to_idx:
                self.word_frequencies[word] = 5.0
                
        print("语义空间特征预计算完成")
        
    def _is_valid_noun(self, word: str) -> bool:
        """检查是否为有效名词"""
        word_lower = word.lower()
        
        # 排除明显的问题词
        problem_words = {'https', 'http', 'www', 'com', 'org', 'net', 'edu', 'gov'}
        if word_lower in problem_words:
            return False
            
        # 排除首字母大写的词汇（可能是人名或专有名词）
        if word[0].isupper() and len(word) > 1:
            return False
            
        # 排除全大写的词汇
        if word.isupper():
            return False
            
        # 排除包含连字符的复合词
        if '-' in word:
            return False
            
        # 排除包含下划线的词汇
        if '_' in word:
            return False
            
        # 排除包含数字的词汇
        if any(char.isdigit() for char in word):
            return False
            
        # 排除过短的词汇
        if len(word_lower) < 3:
            return False
            
        # 排除过长的词汇（可能是专有名词）
        if len(word_lower) > 12:
            return False
            
        # 使用NLTK进行词性标注
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(word_lower)
                pos_tags = pos_tag(tokens)
                for token, tag in pos_tags:
                    if tag.startswith('NN'):  # 名词标签
                        return True
                return False
            except:
                pass
                
        # 启发式名词检查
        function_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'among', 'between',
            'in', 'on', 'at', 'by', 'for', 'to', 'from', 'of', 'with', 'without',
            'this', 'that', 'these', 'those', 'there', 'here', 'then', 'when', 'where',
            'not', 'no', 'nor', 'so', 'too', 'very', 'also', 'either', 'neither',
            'more', 'most', 'less', 'least', 'many', 'much', 'few', 'little',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        if word_lower in function_words:
            return False
            
        # 排除常见动词后缀
        verb_suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'ful', 'less', 'able', 'ible', 'ous', 'al', 'ic']
        for suffix in verb_suffixes:
            if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 2:
                return False
                
        # 排除常见形容词后缀
        adj_suffixes = ['ate', 'ify', 'ise', 'ize', 'ish', 'ive']
        for suffix in adj_suffixes:
            if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 1:
                return False
                
        # 长度检查
        if len(word_lower) < 3:
            return False
            
        return True
        
    def _is_metaphor_friendly(self, word: str) -> bool:
        """检查是否为适合隐喻发散的词汇"""
        word_lower = word.lower()
        
        # 排除文件后缀和技术术语
        file_extensions = {
            'json', 'xml', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c', 'h',
            'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'jpg', 'jpeg', 'png', 'gif', 'svg', 'mp4', 'avi', 'mp3', 'wav',
            'zip', 'rar', 'tar', 'gz', 'exe', 'dll', 'so', 'dylib'
        }
        
        if word_lower in file_extensions:
            logging.info(f"BlindV4 file extension filtered word='{word_lower}'")
            return False
        
        # 排除不适合隐喻的词汇类型
        metaphor_unfriendly = {
            # 人名
            'grant', 'taylor', 'wilson', 'brown', 'smith', 'jones', 'davis', 'miller',
            'garcia', 'rodriguez', 'martinez', 'hernandez', 'lopez', 'gonzalez',
            'anderson', 'thomas', 'jackson', 'white', 'harris', 'clark', 'lewis',
            'robinson', 'walker', 'perez', 'hall', 'young', 'allen', 'sanchez',
            'wright', 'king', 'scott', 'green', 'baker', 'adams', 'nelson',
            
            # 文档类型
            'comments', 'statements', 'reports', 'notes', 'documents', 'papers',
            'articles', 'reviews', 'analyses', 'studies', 'research', 'findings',
            
            # 功能词
            'write', 'ever', 'all', 'use', 'depends', 'affect', 'protect', 'prove',
            'excellent', 'attempts', 'effort', 'rate', 'size', 'transportation',
            
            # 时间相关
            'year', 'month', 'week', 'day', 'hour', 'minute', 'second',
            
            # 其他不适合的词汇
            'human', 'labour', 'sale', 'raw', 'records', 'breakfast', 'burn',
            'reuse', 'open', 'source', 'tools', 'songs', 'arts',
            'employment', 'development', 'customers', 'users', 'members',
            'stations', 'team', 'cable', 'internet', 'technology', 'data',
            'information', 'statistics', 'analysis', 'software', 'science',
            'medicine', 'literature', 'culture', 'health', 'school', 'student',
            'leadership', 'group', 'friends', 'house', 'hero', 'girlfriend'
        }
        
        if word_lower in metaphor_unfriendly:
            logging.info(f"BlindV4 blacklist filtered word='{word_lower}'")
            return False
            
        # 检查是否为常见的专有名词
        if word_lower in ['apple', 'google', 'microsoft', 'amazon', 'facebook', 'twitter']:
            logging.info(f"BlindV4 proper-noun filtered word='{word_lower}'")
            return False
            
        return True
        
    def _is_morphologically_similar(self, word1: str, word2: str) -> bool:
        """检查两个词是否形态相似"""
        w1, w2 = word1.lower(), word2.lower()
        
        # 完全相同
        if w1 == w2:
            return True
            
        # 检查词干相似性
        def get_stems(word):
            stems = {word}
            # 常见词形变化规则
            if word.endswith('s') and len(word) > 3:
                stems.add(word[:-1])
            if word.endswith('es') and len(word) > 4:
                stems.add(word[:-2])
            if word.endswith('ies') and len(word) > 4:
                stems.add(word[:-3] + 'y')
            if word.endswith('ing') and len(word) > 5:
                stems.add(word[:-3])
            if word.endswith('ed') and len(word) > 4:
                stems.add(word[:-2])
            # 添加更多词形变化规则
            if word.endswith('er') and len(word) > 4:
                stems.add(word[:-2])
            if word.endswith('est') and len(word) > 5:
                stems.add(word[:-3])
            if word.endswith('ly') and len(word) > 4:
                stems.add(word[:-2])
            return stems
            
        stems1 = get_stems(w1)
        stems2 = get_stems(w2)
        
        # 检查是否有共同词干
        common_stems = stems1.intersection(stems2)
        if len(common_stems) > 0:
            return True
            
        # 检查是否为单复数关系
        if (w1.endswith('s') and w1[:-1] == w2) or (w2.endswith('s') and w2[:-1] == w1):
            return True
            
        # 检查是否为词形变化（如friend -> friendly）
        if len(w1) > 3 and len(w2) > 3:
            if w1.startswith(w2) or w2.startswith(w1):
                return True
                
        # 检查是否为复数形式（更严格的检查）
        def is_plural(word):
            """检查是否为复数形式"""
            if word.endswith('s'):
                # 检查去掉s后是否为有效词干
                stem = word[:-1]
                if len(stem) >= 3:
                    # 常见的复数规则
                    if stem.endswith('y') and len(stem) > 3:
                        # city -> cities, family -> families
                        return True
                    elif stem.endswith('f') and len(stem) > 3:
                        # leaf -> leaves, wolf -> wolves
                        return True
                    elif stem.endswith('fe') and len(stem) > 4:
                        # knife -> knives, life -> lives
                        return True
                    elif stem.endswith('o') and len(stem) > 2:
                        # potato -> potatoes, tomato -> tomatoes
                        return True
                    else:
                        # 一般规则：直接加s
                        return True
            return False
            
        # 如果任一词汇是复数形式，且与输入词相似，则认为是形态相似
        if is_plural(w1) or is_plural(w2):
            # 检查复数词干是否与输入词相似
            stem1 = w1[:-1] if w1.endswith('s') else w1
            stem2 = w2[:-1] if w2.endswith('s') else w2
            # 这里我们检查词干是否相同，而不是与输入词比较
            if stem1 == stem2:
                return True
                
        return False
        
    def _gene_mutation_strategy(self, input_vec: np.ndarray) -> List[np.ndarray]:
        """基因突变策略：模拟生物基因突变"""
        mutated_vectors = []
        
        for rate, weight in zip(self.params['mutation_rates'], self.params['mutation_weights']):
            # 生成随机扰动向量
            noise = np.random.randn(input_vec.shape[0]).astype(np.float32)
            noise = noise / (np.linalg.norm(noise) + 1e-12)  # 单位化
            
            # 应用突变
            mutated = input_vec + rate * noise
            mutated = mutated / (np.linalg.norm(mutated) + 1e-12)  # 重新单位化
            
            # 根据权重生成多个变体
            num_variants = max(1, int(weight * 6))  # 减少变体数量以提高速度
            for _ in range(num_variants):
                mutated_vectors.append(mutated)
                
        return mutated_vectors
        
    def _niche_exploration_strategy(self, input_vec: np.ndarray) -> List[np.ndarray]:
        """生态位探索策略：寻找语义空间中的稀疏区域"""
        # 计算所有词向量与输入向量的距离
        similarities = np.dot(self.embeddings, input_vec)
        
        # 找到中等相似度的词（生态位区域）
        min_sim = self.params['min_similarity']
        max_sim = self.params['max_similarity']
        niche_mask = (similarities >= min_sim) & (similarities <= max_sim)
        
        # 随机选择一些生态位向量
        niche_indices = np.where(niche_mask)[0]
        if len(niche_indices) > 0:
            # 随机选择最多3个生态位向量
            num_niche = min(3, len(niche_indices))
            selected_indices = np.random.choice(niche_indices, num_niche, replace=False)
            niche_vectors = [self.embeddings[idx] for idx in selected_indices]
        else:
            niche_vectors = []
            
        return niche_vectors
        
    def _adaptive_radiation_strategy(self, input_vec: np.ndarray) -> List[np.ndarray]:
        """适应性辐射策略：从一个种子点爆发出多方向的变异"""
        radiation_vectors = []
        
        # 生成多个辐射方向
        for i in range(self.params['radiation_directions']):
            # 生成随机方向向量
            direction = np.random.randn(input_vec.shape[0]).astype(np.float32)
            direction = direction / (np.linalg.norm(direction) + 1e-12)
            
            # 确保方向与输入向量正交
            projection = np.dot(direction, input_vec)
            direction = direction - projection * input_vec
            direction = direction / (np.linalg.norm(direction) + 1e-12)
            
            # 应用辐射强度
            radiation_vec = input_vec + self.params['radiation_strength'] * direction
            radiation_vec = radiation_vec / (np.linalg.norm(radiation_vec) + 1e-12)
            
            radiation_vectors.append(radiation_vec)
            
        return radiation_vectors
        
    def _find_candidate_words(self, target_vec: np.ndarray, exclude_words: Set[str], top_k: int = 20) -> List[Tuple[str, float]]:
        """找到候选词"""
        similarities = np.dot(self.embeddings, target_vec)
        
        # 排除已选择的词
        for word in exclude_words:
            if word in self.word_to_idx:
                idx = self.word_to_idx[word]
                similarities[idx] = -1.0
                
        # 找到最相似的词
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
        
        results = []
        for idx in top_indices:
            word = self.idx_to_word[idx]
            similarity = similarities[idx]
            
            # 检查是否为有效名词
            if self._is_valid_noun(word):
                # 词频过滤
                freq = self.word_frequencies.get(word, 5.0)
                if freq >= self.params['min_zipf']:
                    results.append((word, similarity))
                    
        return results
        
    def blind_variation_generate(self, input_word: str) -> List[Tuple[str, float]]:
        """主生成函数"""
        print(f"处理输入词: {input_word}")
        
        # 标准化输入词
        input_word_lower = input_word.lower().strip()
        if input_word_lower not in self.word_to_idx:
            print(f"警告：词汇 '{input_word}' 不在词向量模型中")
            return []
            
        input_idx = self.word_to_idx[input_word_lower]
        input_vec = self.embeddings[input_idx]
        
        print(f"输入词向量索引: {input_idx}")
        
        # 策略1：基因突变类比
        print("应用基因突变策略...")
        mutation_vectors = self._gene_mutation_strategy(input_vec)
        print(f"生成了 {len(mutation_vectors)} 个突变向量")
        
        # 策略2：生态位探索
        print("应用生态位探索策略...")
        niche_vectors = self._niche_exploration_strategy(input_vec)
        print(f"生成了 {len(niche_vectors)} 个生态位向量")
        
        # 策略3：适应性辐射
        print("应用适应性辐射策略...")
        radiation_vectors = self._adaptive_radiation_strategy(input_vec)
        print(f"生成了 {len(radiation_vectors)} 个辐射向量")
        
        # 合并所有策略生成的向量
        all_vectors = mutation_vectors + niche_vectors + radiation_vectors
        print(f"总共生成了 {len(all_vectors)} 个候选向量")
        
        # 为每个向量找到最接近的词
        all_candidates = []
        exclude_words = {input_word_lower}
        
        for vec in all_vectors:
            candidates = self._find_candidate_words(vec, exclude_words, top_k=10)
            all_candidates.extend(candidates)
            
        # 去重并过滤
        unique_candidates = {}
        seen_lowercase = set()  # 用于检测大小写重复
        
        for word, similarity in all_candidates:
            word_lower = word.lower()
            
            # 跳过首字母大写或全大写的词汇
            if word[0].isupper() or word.isupper():
                continue
                
            # 检查是否已经见过相同的小写形式
            if word_lower in seen_lowercase:
                continue
                
            # 检查与输入词的形态相似性
            if not self._is_morphologically_similar(word, input_word_lower):
                # 检查是否为隐喻友好的词汇
                if self._is_metaphor_friendly(word):
                    # 额外检查：避免复数形式
                    def is_likely_plural(word):
                        """检查是否可能是复数形式"""
                        if not word.endswith('s'):
                            return False
                        # 检查去掉s后是否为有效词干
                        stem = word[:-1]
                        if len(stem) < 3:
                            return False
                        # 如果词干与输入词相同，则认为是复数
                        if stem == input_word_lower:
                            return True
                        # 检查常见的复数模式
                        if stem.endswith('y') and len(stem) > 3:
                            return True
                        if stem.endswith('f') and len(stem) > 3:
                            return True
                        if stem.endswith('fe') and len(stem) > 4:
                            return True
                        if stem.endswith('o') and len(stem) > 2:
                            return True
                        # 一般规则：如果词干长度合理，可能是复数
                        if len(stem) >= 4:
                            return True
                        return False
                    
                    if not is_likely_plural(word):
                        unique_candidates[word] = similarity
                        seen_lowercase.add(word_lower)
                    
        candidates_list = list(unique_candidates.items())
        
        # 计算多样性分数
        diversity_scores = []
        for i, (word1, sim1) in enumerate(candidates_list):
            word1_idx = self.word_to_idx[word1]
            vec1 = self.embeddings[word1_idx]
            
            # 计算与其他候选词的相似度
            similarities = []
            for j, (word2, sim2) in enumerate(candidates_list):
                if i != j:
                    word2_idx = self.word_to_idx[word2]
                    vec2 = self.embeddings[word2_idx]
                    similarity = np.dot(vec1, vec2)
                    similarities.append(similarity)
                    
            # 多样性分数 = 1 - 平均相似度
            if similarities:
                avg_similarity = np.mean(similarities)
                diversity_score = 1.0 - avg_similarity
            else:
                diversity_score = 1.0
                
            diversity_scores.append(diversity_score)
        
        # 综合评分：相似度 + 多样性 + 词频
        final_scores = []
        for i, (word, similarity) in enumerate(candidates_list):
            diversity = diversity_scores[i]
            freq = self.word_frequencies.get(word, 5.0)
            
            # 综合分数 = 相似度 * 0.3 + 多样性 * 0.5 + 词频 * 0.2
            final_score = similarity * 0.3 + diversity * 0.5 + (freq / 10.0) * 0.2
            final_scores.append((word, final_score))
            
        # 按分数排序
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 多样性过滤：确保结果间相似度不超过阈值
        selected_results = []
        selected_vectors = []
        
        for word, score in final_scores:
            if len(selected_results) >= self.params['top_k']:
                break
                
            word_idx = self.word_to_idx[word]
            word_vec = self.embeddings[word_idx]
            
            # 检查与已选择结果的相似度
            too_similar = False
            for selected_vec in selected_vectors:
                similarity = np.dot(word_vec, selected_vec)
                if similarity > self.params['diversity_threshold']:
                    too_similar = True
                    break
                    
            if not too_similar:
                selected_results.append((word, score))
                selected_vectors.append(word_vec)
                
        # 若结果不足最小数量，进行回退补齐：
        min_results = int(self.params.get('min_results', 3))
        if len(selected_results) < min_results:
            # 策略A：从未选中的高分候选中补齐（放宽多样性约束）
            remaining = []
            for w, sc in final_scores:
                if all(w != sw for sw, _ in selected_results):
                    remaining.append((w, sc))
            for w, sc in remaining:
                selected_results.append((w, sc))
                if len(selected_results) >= min_results:
                    break

        # 若仍不足，策略B：对已选结果做“二级发散”（最多一层）
        if len(selected_results) < min_results:
            fallback_depth = int(self.params.get('max_fallback_depth', 1))
            used_words = set(sw for sw, _ in selected_results)
            for _ in range(fallback_depth):
                seeds = [sw for sw, _ in selected_results]
                for seed in seeds:
                    if seed not in self.word_to_idx:
                        continue
                    seed_idx = self.word_to_idx[seed]
                    seed_vec = self.embeddings[seed_idx]
                    # 针对seed进行一次小幅发散（复用候选检索 + 过滤）
                    seed_candidates = self._find_candidate_words(seed_vec, exclude_words | used_words, top_k=10)
                    for w, sim in seed_candidates:
                        if w in used_words:
                            continue
                        # 走相同过滤：形态 + 隐喻友好 + 复数
                        if self._is_morphologically_similar(w, input_word_lower):
                            continue
                        if not self._is_metaphor_friendly(w):
                            continue
                        if len(w) > 4 and w.endswith('s'):
                            continue
                        selected_results.append((w, sim))
                        used_words.add(w)
                        if len(selected_results) >= min_results:
                            break
                    if len(selected_results) >= min_results:
                        break

        print(f"最终选择了 {len(selected_results)} 个结果")
        return selected_results


def main():
    """主测试函数"""
    print("=== Blind Variation V4（优化版）===")
    
    # 创建生成器
    generator = OptimizedBlindVariation()
    
    # 测试词汇
    test_words = ["ocean", "mountain", "fire", "wind", "city", "computer", "technology", "data"]
    
    for word in test_words:
        print("\n" + "=" * 60)
        print(f"测试输入词: {word}")
        print("=" * 60)
        
        start_time = time.time()
        results = generator.blind_variation_generate(word)
        end_time = time.time()
        
        print(f"计算时间: {end_time - start_time:.3f} 秒")
        print(f"结果数量: {len(results)}")
        
        if results:
            print("\n最优发散词汇:")
            print("-" * 40)
            for i, (result_word, score) in enumerate(results, 1):
                print(f"{i:2d}. {result_word:15s} (综合分数: {score:.4f})")
        else:
            print("没有找到合适的结果")


if __name__ == "__main__":
    main()
