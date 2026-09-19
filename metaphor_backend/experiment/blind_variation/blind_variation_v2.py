#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blind Variation 词义发散算法 - V2（快速基线版）

目标：在大词表（~50k x 300）下实现“快速但有效”的单词级突变，优先保证速度与可产出，
并在生物启发策略（突变 + 多样性 + 轻量选择压力）的指引下得到高异质性的结果。

设计取舍：
- 不做昂贵的多轮候选生成与逐候选近邻检索；改为一次性全库相似度向量化计算（E @ v0），
  在窗口内（相关但不过近）直接选择候选；再用多样性选择（MMR/阈值）得到 top_k。
- 轻量词性与形态过滤（NLTK 不可用时用启发式），避免重型外部依赖；
- 参数温和，确保在大多数词上都能“快速产出”。

运行复杂度：
- 主要成本为一次 E @ v0（50k x 300 的矩阵-向量乘），配合 argpartition/排序与少量多样性筛选；
  实测通常 < 1 秒（具体取决于 BLAS 与硬件）。
"""

import os
import pickle
import re
import unicodedata
from typing import Dict, List, Tuple, Any

import numpy as np

# 可选的 NLTK 支持（科研级词性/词形）
try:
    import nltk  # noqa: F401
    from nltk.corpus import wordnet as wn
    NLTK_AVAILABLE = True
    try:
        wn.synsets('test')
    except LookupError:
        # 若未下载语料，后续会提示用户下载
        NLTK_AVAILABLE = True
except Exception:
    wn = None  # type: ignore
    NLTK_AVAILABLE = False

# 可选的词频过滤（无需外部语料，适合离线环境）
try:
    from wordfreq import zipf_frequency  # noqa: F401
    WORDFREQ_AVAILABLE = True
except Exception:
    zipf_frequency = None  # type: ignore
    WORDFREQ_AVAILABLE = False


DEFAULT_PARAMS = {
    # 相似度窗口（控制“相关但不过近”）
    's_min': 0.20,
    's_max': 0.70,

    # 选择与多样性
    'top_pool': 1200,          # 先挑出前 N 个候选再做多样性（避免全排序）
    'top_k': 5,                # 返回数量
    'diversity_threshold': 0.62,  # 结果间最大相似度（越小越分散）
    'alpha': 0.6,              # 新颖性权重（越大越偏远）
    'gamma': 0.2,              # 数据事实相关性加分权重

    # 词性与形态
    'enable_pos': True,        # 启用名词检查（无 NLTK 时使用启发式）
    'min_zipf': 3.8,           # 最小 Zipf 词频阈值（需安装 wordfreq 才生效）

    # v3 相关参数（多尺度 + 锚点 + 重组 + MMR）
    'near_low': 0.55, 'near_high': 0.70,
    'mid_low':  0.35, 'mid_high':  0.55,
    'far_low':  0.20, 'far_high':  0.35,
    'top_pool_near': 400,
    'top_pool_mid':  500,
    'top_pool_far':  500,
    'num_anchors':    6,
    'N_near':         20,
    'N_seg':          6,
    'delta_small':    0.08,   # 小幅突变幅度
    'lambda_segment': 0.8,    # 段突变强度
    'r_side':         0.15,   # 段突变横向扰动
    'betas':          [0.6, 0.75, 0.85],
    'decode_k':       5,
    'mmr_lambda':     0.7,
    'rarity_weight':  0.15,
    'band_weights':   {'near': 0.10, 'mid': 0.20, 'far': 0.30},
    'num_niches':     6
}


DATA_FACT_CATEGORIES = {
    'Extremum': ['peak', 'valley', 'summit', 'bottom', 'maximum', 'minimum'],
    'Distribution': ['spread', 'cluster', 'scatter', 'concentrate', 'distribute'],
    'Correlation': ['link', 'connect', 'relate', 'associate', 'correlate'],
    'Trend': ['flow', 'stream', 'current', 'direction', 'movement'],
    'Growth': ['expand', 'grow', 'increase', 'multiply', 'proliferate']
}


class BlindVariationGeneratorV2(object):
    """快速突变生成器（V2 基线）"""

    def __init__(self, embeddings_path=None, params=None):
        self.params = dict(DEFAULT_PARAMS)
        if params:
            self.params.update(params)

        self.word_to_idx = {}
        self.idx_to_word = {}
        self.embeddings = np.zeros((0, 0), dtype=np.float32)
        self._noun_cache = {}
        self._function_words = set([
            'a','an','the','and','or','but','if','because','among','between','before','after','above','below',
            'in','on','at','by','for','to','from','of','with','without','into','onto','as','than','that','which',
            'this','these','those','there','here','then','when','while','where','who','whom','whose','why','how',
            'not','no','nor','so','too','very','also','either','neither','both','each','every','some','any','such',
            'more','most','less','least','many','much','few','little','other','another','same','own',
            # 常见星期/月缩写等
            'mon','tue','wed','thu','fri','sat','sun','jan','feb','mar','apr','jun','jul','aug','sep','oct','nov','dec'
        ])
        # 额外噪声/俗语/平台专有词拦截
        self._noise_words = set([
            'btw','aka','etc','vs','imo','idk','lol','omg','wtf','thx','pls','ok','okay','hello','hi','bye',
            'sub','vol','sim','alt','navbox','wikipedia','wikidata','gimme','wizardman','arbcom','bjaodn',
            'wrestlemania','rjensen','nomination'  # 可扩展
        ])

        if embeddings_path:
            self.load_embeddings(embeddings_path)
        else:
            # 优先使用缓存；若没有则使用示例向量（小词表）
            cache_path = "data/fasttext_cache.pkl"
            vec_path = "data/wiki-news-300d-1M.vec"
            if os.path.exists(cache_path):
                self.load_embeddings(cache_path)
            elif os.path.exists(vec_path):
                self.load_embeddings(vec_path)
            else:
                self._create_sample_embeddings()

    # ---------------- Embedding I/O -----------------
    def load_embeddings(self, path):
        print("正在加载词向量模型: {}".format(path))
        if path.endswith('.pkl'):
            self._load_from_cache(path)
        elif path.endswith('.vec'):
            self._load_from_vec(path)
        else:
            # 兜底：示例
            self._create_sample_embeddings()

        # 规范化为 float32 且每行单位化
        if self.embeddings.dtype != np.float32:
            self.embeddings = self.embeddings.astype(np.float32)
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
        self.embeddings = self.embeddings / norms
        print("词向量模型加载完成，词汇量: {}".format(len(self.word_to_idx)))

    def _load_from_cache(self, cache_path):
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        self.word_to_idx = data['word_to_idx']
        self.embeddings = data['embeddings']
        self.idx_to_word = data['idx_to_word']
        print("成功从缓存加载词向量: {}".format(cache_path))

    def _load_from_vec(self, vec_path):
        # 只加载前 50k 以控制内存/速度
        max_vocab = 50000
        word_to_idx = {}
        idx_to_word = {}
        vectors = []
        with open(vec_path, 'r', encoding='utf-8', errors='ignore') as f:
            header = f.readline()
            for i, line in enumerate(f):
                if i >= max_vocab:
                    break
                parts = line.strip().split()
                if len(parts) < 10:
                    continue
                word = parts[0]
                try:
                    vec = np.array([float(x) for x in parts[1:]], dtype=np.float32)
                except Exception:
                    continue
                idx = len(vectors)
                word_to_idx[word] = idx
                idx_to_word[idx] = word
                vectors.append(vec)
        if not vectors:
            self._create_sample_embeddings()
            return
        self.embeddings = np.vstack(vectors).astype(np.float32)
        self.word_to_idx = word_to_idx
        self.idx_to_word = idx_to_word
        print("成功从 .vec 加载词向量: {} ({} entries)".format(vec_path, len(self.word_to_idx)))

    def _create_sample_embeddings(self):
        words = [
            'ocean','sea','river','lake','wave','current','tide','shore','reef',
            'mountain','peak','valley','cliff','rock','stone','ridge',
            'city','town','village','street','bridge','harbor',
            'computer','device','machine','engine','network','data','analysis','model',
            'fire','flame','heat','light','energy',
            'wind','storm','breeze','cloud','rain',
        ]
        np.random.seed(42)
        dim = 100
        E = np.random.randn(len(words), dim).astype(np.float32)
        E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-12)
        self.embeddings = E
        self.word_to_idx = {w: i for i, w in enumerate(words)}
        self.idx_to_word = {i: w for w, i in self.word_to_idx.items()}
        print("使用示例词向量（{} 词, {} 维）".format(len(words), dim))

    # ---------------- Heuristics -----------------
    def _heuristic_noun_check(self, word):
        wl = word.lower()
        if wl in self._function_words:
            return False
        if wl in self._noise_words:
            return False
        non_noun_suffixes = ['ing', 'ed', 'ly', 'ful', 'less', 'able', 'ible', 'ous', 'al', 'ic']
        for suf in non_noun_suffixes:
            if wl.endswith(suf) and len(wl) > len(suf) + 2:
                return False
        # 常见动词/形容词后缀（更严格排除）
        verb_adj_suffixes = ['ate','ify','ise','ize','ish','ive']
        for suf in verb_adj_suffixes:
            if wl.endswith(suf) and len(wl) > len(suf) + 1:
                return False
        # 常见民族/形容词后缀
        if (wl.endswith('ian') or wl.endswith('ean')) and len(wl) > 4:
            return False
        non_nouns = {
            'is','are','was','were','be','been','have','has','had','do','does','did',
            'very','much','many','few','little','big','small','good','bad'
        }
        return wl not in non_nouns

    def _wordnet_noun(self, word):
        if not NLTK_AVAILABLE or wn is None:
            return False
        try:
            return len(wn.synsets(word, pos=wn.NOUN)) > 0
        except Exception:
            return False

    def _wordnet_lemma(self, word):
        if not NLTK_AVAILABLE or wn is None:
            return None
        try:
            lemma = wn.morphy(word, wn.NOUN)
            return lemma
        except Exception:
            return None

    def _to_ascii_lower(self, token):
        # 去除重音符，转 ascii，小写
        norm = unicodedata.normalize('NFKD', token)
        ascii_str = norm.encode('ascii', 'ignore').decode('ascii')
        ascii_str = ascii_str.strip().lower()
        return ascii_str

    def _lemma_plural(self, token_lower):
        # 简单名词还原（复数→单数）
        if len(token_lower) >= 4 and token_lower.endswith('ies'):
            return token_lower[:-3] + 'y'
        for suf in ['ses', 'xes', 'zes', 'ches', 'shes']:
            if token_lower.endswith(suf) and len(token_lower) > len(suf) + 1:
                return token_lower[:-2]
        if token_lower.endswith('s') and not token_lower.endswith('ss') and len(token_lower) > 3:
            return token_lower[:-1]
        return token_lower

    def _normalize_base_noun(self, token):
        # 统一：小写、ASCII，仅字母、简易单数化，并通过名词启发式
        ascii_lower = self._to_ascii_lower(token)
        if not re.fullmatch(r'[a-z]+', ascii_lower or ''):
            return None
        if len(ascii_lower) < 3:
            return None
        # 优先用 WordNet 词形
        lemma = self._wordnet_lemma(ascii_lower) if NLTK_AVAILABLE else None
        if lemma is None:
            lemma = self._lemma_plural(ascii_lower)
        if not self._heuristic_noun_check(lemma):
            return None
        # 词频过滤：过低词频多为人名/稀有专名
        if WORDFREQ_AVAILABLE:
            try:
                if zipf_frequency(lemma, 'en') < float(self.params.get('min_zipf', 3.2)):
                    return None
            except Exception:
                pass
        return lemma

    def _is_noun(self, word):
        wl = word.lower()
        if wl in self._noun_cache:
            return self._noun_cache[wl]
        res = False
        if NLTK_AVAILABLE and self._wordnet_noun(wl):
            res = True
        else:
            res = self._heuristic_noun_check(wl)
        self._noun_cache[wl] = res
        return res

    def _morphologically_similar(self, a, b):
        a = a.lower(); b = b.lower()
        if a == b:
            return True
        def stems(x):
            forms = {x}
            rules = [('ies','y'),('es',''),('s',''),('ing',''),('ed',''),('er',''),('est','')]
            for suf, rep in rules:
                if x.endswith(suf) and len(x) > len(suf) + 1:
                    forms.add(x[:-len(suf)] + rep)
            return list(forms)
        sa = set(stems(a)); sb = set(stems(b))
        return len(sa.intersection(sb)) > 0

    def _data_fact_score(self, token):
        # 短语取 head
        head = token.split()[-1].lower()
        for _, words in DATA_FACT_CATEGORIES.items():
            if head in [w.lower() for w in words]:
                return 1.0
        return 0.0

    # ---------------- Core: Fast Mutation -----------------
    def blind_variation_generate(self, input_word):
        lw = input_word.lower()
        norm_input = self._normalize_base_noun(input_word) or lw
        # 输入向量优先使用标准化词条
        key_for_vec = norm_input if norm_input in self.word_to_idx else lw
        if key_for_vec not in self.word_to_idx:
            print("警告：词汇 '{}' 不在词向量模型中".format(input_word))
            return []

        idx = self.word_to_idx[key_for_vec]
        v0 = self.embeddings[idx]

        # 一次性全库相似度（已单位化，可用点积近似余弦）
        sims = np.dot(self.embeddings, v0).astype(np.float32)  # shape: (V,)

        # 相似度窗口过滤（相关但不过近）
        s_min = float(self.params['s_min'])
        s_max = float(self.params['s_max'])
        mask = (sims >= s_min) & (sims <= s_max)
        mask[idx] = False  # 去除自身

        # 先按“新颖性优先”的打分挑出一个候选池
        alpha = float(self.params['alpha'])
        gamma = float(self.params['gamma'])
        novelty = 1.0 - sims  # 越大越新
        # 基础 fitness = alpha*novelty + (1-alpha)*relevance(sims)
        base_fit = alpha * novelty + (1.0 - alpha) * sims

        # 仅在掩码内取 top_pool 个索引
        pool_size = int(self.params['top_pool'])
        masked_idx = np.where(mask)[0]
        if masked_idx.size == 0:
            # 放宽策略：若完全无候选，则退一步取最不相似的少量词
            k = min(pool_size, sims.shape[0] - 1)
            pool_idx = np.argpartition(novelty, -k)[-k:]
        else:
            masked_fit = base_fit[masked_idx]
            k = min(pool_size, masked_fit.shape[0])
            if k <= 0:
                return []
            top_rel = np.argpartition(masked_fit, -k)[-k:]
            pool_idx = masked_idx[top_rel]

        # 细化排序：按 fitness 降序
        pool_fit = base_fit[pool_idx]
        order = np.argsort(pool_fit)[::-1]
        pool_idx = pool_idx[order]
        pool_fit = pool_fit[order]

        # 轻量过滤：名词 + 形态差异 + 统一小写原型
        filtered_tokens = []  # type: List[Tuple[str, float, int]]
        seen_norm = set()
        for i in pool_idx:
            w = self.idx_to_word[int(i)]
            norm_w = self._normalize_base_noun(w)
            if norm_w is None:
                continue
            if self.params.get('enable_pos', True) and not self._is_noun(norm_w):
                continue
            if self._morphologically_similar(norm_w, norm_input):
                continue
            if len(norm_w) < 3:
                continue
            if norm_w in seen_norm:
                continue
            # 数据事实加分
            fit = float(pool_fit[np.where(pool_idx == i)[0][0]]) + gamma * self._data_fact_score(w)
            filtered_tokens.append((norm_w, fit, int(i)))
            seen_norm.add(norm_w)
            if len(filtered_tokens) >= max(self.params['top_k'] * 20, 50):
                # 足量后不再扩大池
                break

        if not filtered_tokens:
            return []

        # 多样性选择：贪心，约束两两相似度 <= 阈值
        div_thr = float(self.params['diversity_threshold'])
        top_k = int(self.params['top_k'])
        selected = []       # type: List[Tuple[str, float]]
        selected_vecs = []  # type: List[np.ndarray]
        for w, fit, i in filtered_tokens:
            vi = self.embeddings[i]
            ok = True
            for sv in selected_vecs:
                if float(np.dot(vi, sv)) > div_thr:
                    ok = False
                    break
            if ok:
                selected.append((w, float(fit)))
                selected_vecs.append(vi)
                if len(selected) >= top_k:
                    break

        # 如果多样性约束导致不足，则从余下的按分数补齐
        if len(selected) < top_k:
            for w, fit, _ in filtered_tokens:
                if all(w != sw for sw, _ in selected):
                    selected.append((w, float(fit)))
                    if len(selected) >= top_k:
                        break

        return selected[:top_k]


def main():
    print("=== Blind Variation V2（快速基线）===")
    gen = BlindVariationGeneratorV2()
    test_words = ["ocean", "mountain", "fire", "wind", "city", "computer", "technology", "data"]
    for w in test_words:
        print("\n" + "=" * 50)
        print("输入: {}".format(w))
        res = gen.blind_variation_generate(w)
        if not res:
            print("无结果")
        else:
            for i, (tok, fit) in enumerate(res, 1):
                print("{:2d}. {:15s} (适应度: {:.4f})".format(i, tok, fit))


if __name__ == "__main__":
    main()


