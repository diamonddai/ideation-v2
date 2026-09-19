#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blind Variation 词义发散算法 - V3（生物启发版）

集成了3个核心生物启发策略：
1. 基因突变类比：模拟生物基因突变，引入不同幅度的语义扰动
2. 生态位探索：优先搜索语义空间中稀疏、少被占据的区域  
3. 适应性辐射：从一个种子点爆发出多方向的变异
"""

import os
import pickle
import re
import time
from typing import Dict, List, Tuple, Any, Set
from collections import defaultdict

import numpy as np
from scipy.spatial.distance import cosine
from sklearn.cluster import KMeans

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


class BioInspiredBlindVariation:
    """生物启发的Blind Variation算法"""
    
    def __init__(self, embeddings_path=None, params=None):
        # 默认参数配置
        self.default_params = {
            # 基因突变策略参数
            'mutation_rates': [0.1, 0.3, 0.6],  # 小、中、大幅突变率
            'mutation_weights': [0.4, 0.4, 0.2],  # 各突变类型的权重
            
            # 生态位探索参数
            'niche_clusters': 8,  # 语义簇数量
            'sparsity_threshold': 0.15,  # 稀疏度阈值
            
            # 适应性辐射参数
            'radiation_directions': 12,  # 辐射方向数
            'radiation_strength': 0.5,  # 辐射强度
            'diversity_threshold': 0.65,  # 多样性阈值
            
            # 通用参数
            'top_k': 5,  # 返回结果数
            'min_zipf': 4.0,  # 最小词频阈值
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
            self.load_embeddings(cache_path)
        else:
            self._create_sample_embeddings()
            
    def _create_sample_embeddings(self):
        """创建示例词向量"""
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
        print(f"使用示例词向量（{len(words)} 词, {dim} 维）")
        
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
            num_variants = max(1, int(weight * 10))
            for _ in range(num_variants):
                mutated_vectors.append(mutated)
                
        return mutated_vectors
        
    def _niche_exploration_strategy(self, input_vec: np.ndarray) -> List[np.ndarray]:
        """生态位探索策略：寻找语义空间中的稀疏区域"""
        # 使用K-means聚类找到语义簇
        kmeans = KMeans(n_clusters=self.params['niche_clusters'], random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(self.embeddings)
        
        # 计算每个簇的密度
        cluster_densities = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            cluster_densities[label].append(i)
            
        # 找到稀疏的簇（密度低的簇）
        sparse_clusters = []
        for label, indices in cluster_densities.items():
            if len(indices) < len(self.embeddings) / self.params['niche_clusters'] * 0.5:
                sparse_clusters.append(label)
                
        # 在稀疏簇中寻找候选向量
        niche_vectors = []
        for cluster_label in sparse_clusters:
            cluster_indices = cluster_densities[cluster_label]
            if cluster_indices:
                # 选择簇中距离输入向量最远的点
                cluster_vectors = self.embeddings[cluster_indices]
                distances = [cosine(input_vec, vec) for vec in cluster_vectors]
                farthest_idx = np.argmax(distances)
                niche_vectors.append(cluster_vectors[farthest_idx])
                
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
        
    def _find_nearest_words(self, target_vec: np.ndarray, exclude_words: Set[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """找到最接近目标向量的词"""
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
        
    def _calculate_diversity_score(self, candidates: List[Tuple[str, float]]) -> List[float]:
        """计算多样性分数"""
        if len(candidates) <= 1:
            return [1.0] * len(candidates)
            
        diversity_scores = []
        for i, (word1, sim1) in enumerate(candidates):
            word1_idx = self.word_to_idx[word1]
            vec1 = self.embeddings[word1_idx]
            
            # 计算与其他候选词的相似度
            similarities = []
            for j, (word2, sim2) in enumerate(candidates):
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
            
        return diversity_scores
        
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
            candidates = self._find_nearest_words(vec, exclude_words, top_k=5)
            all_candidates.extend(candidates)
            
        # 去重并计算多样性分数
        unique_candidates = {}
        for word, similarity in all_candidates:
            if word not in unique_candidates:
                unique_candidates[word] = similarity
                
        candidates_list = list(unique_candidates.items())
        
        # 计算多样性分数
        diversity_scores = self._calculate_diversity_score(candidates_list)
        
        # 综合评分：相似度 + 多样性 + 词频
        final_scores = []
        for i, (word, similarity) in enumerate(candidates_list):
            diversity = diversity_scores[i]
            freq = self.word_frequencies.get(word, 5.0)
            
            # 综合分数 = 相似度 * 0.4 + 多样性 * 0.4 + 词频 * 0.2
            final_score = similarity * 0.4 + diversity * 0.4 + (freq / 10.0) * 0.2
            final_scores.append((word, final_score))
            
        # 按分数排序并返回top_k个结果
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
                
        print(f"最终选择了 {len(selected_results)} 个结果")
        return selected_results


def main():
    """主测试函数"""
    print("=== Blind Variation V3（生物启发版）===")
    
    # 创建生成器
    generator = BioInspiredBlindVariation()
    
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
