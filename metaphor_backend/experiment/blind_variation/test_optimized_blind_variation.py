#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的Blind Variation算法效果
"""

import time
import os
import numpy as np
from blind_variation import BlindVariationGenerator

def test_optimization_effects():
    """测试优化策略的效果"""
    print("=== 优化策略效果测试 ===")
    
    # 创建生成器实例
    generator = BlindVariationGenerator()
    
    # 测试词汇列表
    test_words = ["ocean", "mountain", "fire", "wind", "city", "computer", "technology"]
    
    for test_word in test_words:
        print(f"\n{'='*60}")
        print(f"测试输入词: {test_word}")
        print(f"{'='*60}")
        
        # 生成发散词汇
        start_time = time.time()
        results = generator.blind_variation_generate(test_word)
        end_time = time.time()
        
        print(f"计算时间: {end_time - start_time:.3f} 秒")
        
        if results:
            print(f"\n最优发散词汇（前{len(results)}个）:")
            print("-" * 50)
            for i, (word, fitness) in enumerate(results, 1):
                print(f"{i:2d}. {word:15s} (适应度: {fitness:.4f})")
            
            # 分析结果质量
            analyze_results(generator, test_word, results)
        else:
            print("未找到合适的发散词汇")
        
        print()

def analyze_results(generator, input_word, results):
    """分析结果质量"""
    print(f"\n结果质量分析:")
    
    if not results:
        return
    
    # 获取输入词向量
    input_vec = generator.embeddings[generator.word_to_idx[input_word.lower()]]
    
    # 分析语义相似度分布
    similarities = []
    for word, _ in results:
        if word in generator.word_to_idx:
            word_vec = generator.embeddings[generator.word_to_idx[word]]
            sim = np.dot(input_vec, word_vec) / (np.linalg.norm(input_vec) * np.linalg.norm(word_vec))
            similarities.append(sim)
    
    if similarities:
        print(f"  与输入词的相似度范围: {min(similarities):.3f} - {max(similarities):.3f}")
        print(f"  平均相似度: {np.mean(similarities):.3f}")
        print(f"  相似度标准差: {np.std(similarities):.3f}")
    
    # 分析结果间的多样性
    diversity_scores = []
    for i, (word1, _) in enumerate(results):
        for j, (word2, _) in enumerate(results[i+1:], i+1):
            if word1 in generator.word_to_idx and word2 in generator.word_to_idx:
                vec1 = generator.embeddings[generator.word_to_idx[word1]]
                vec2 = generator.embeddings[generator.word_to_idx[word2]]
                sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                diversity_scores.append(1 - sim)  # 转换为多样性分数
    
    if diversity_scores:
        print(f"  结果间多样性分数: {min(diversity_scores):.3f} - {max(diversity_scores):.3f}")
        print(f"  平均多样性: {np.mean(diversity_scores):.3f}")

def test_parameter_sensitivity():
    """测试参数敏感性"""
    print("\n=== 参数敏感性测试 ===")
    
    test_word = "ocean"
    
    # 测试不同的参数设置
    test_params = [
        {
            'name': '默认优化参数',
            'params': {}
        },
        {
            'name': '高扰动参数',
            'params': {
                'sigma_0': 0.15,
                'delta': 0.8,
                'num_candidates': 150
            }
        },
        {
            'name': '严格过滤参数',
            'params': {
                'similarity_threshold': 0.7,
                'diversity_threshold': 0.8,
                'min_similarity': 0.4
            }
        },
        {
            'name': '宽松过滤参数',
            'params': {
                'similarity_threshold': 0.9,
                'diversity_threshold': 0.5,
                'min_similarity': 0.2
            }
        }
    ]
    
    for test_config in test_params:
        name = test_config['name']
        params = test_config['params']
        
        print(f"\n{name}:")
        print(f"  参数: {params}")
        
        generator = BlindVariationGenerator(params=params)
        results = generator.blind_variation_generate(test_word)
        
        if results:
            print(f"  结果:")
            for i, (word, fitness) in enumerate(results[:3], 1):
                print(f"    {i}. {word:15s} (适应度: {fitness:.4f})")
        else:
            print("  无结果")

def test_comparison_with_original():
    """与原始版本对比测试"""
    print("\n=== 与原始版本对比测试 ===")
    
    test_word = "ocean"
    
    # 创建优化版本生成器
    optimized_generator = BlindVariationGenerator()
    
    # 创建原始版本生成器（使用原始参数）
    original_params = {
        'sigma_0': 0.1,      # 原始突变幅度
        'delta': 0.5,        # 原始漂移幅度
        'num_candidates': 50, # 原始候选数量
        'similarity_threshold': 1.0,  # 不进行语义过滤
        'diversity_threshold': 0.0,   # 不进行多样性控制
        'min_similarity': 0.0         # 不限制最小相似度
    }
    original_generator = BlindVariationGenerator(params=original_params)
    
    print(f"测试词汇: {test_word}")
    
    # 测试优化版本
    print(f"\n优化版本结果:")
    optimized_results = optimized_generator.blind_variation_generate(test_word)
    if optimized_results:
        for i, (word, fitness) in enumerate(optimized_results, 1):
            print(f"  {i}. {word:15s} (适应度: {fitness:.4f})")
    
    # 测试原始版本
    print(f"\n原始版本结果:")
    original_results = original_generator.blind_variation_generate(test_word)
    if original_results:
        for i, (word, fitness) in enumerate(original_results, 1):
            print(f"  {i}. {word:15s} (适应度: {fitness:.4f})")

def main():
    """主函数"""
    print("=== 优化版Blind Variation算法测试 ===")
    print("=" * 60)
    
    # 检查文件状态
    print("检查词向量文件状态:")
    files_to_check = [
        "data/wiki-news-300d-1M.bin",
        "data/fasttext_cache.pkl"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  ✓ {file_path}: {size_mb:.1f} MB")
        else:
            print(f"  ✗ {file_path}: 不存在")
    
    # 运行测试
    test_optimization_effects()
    test_parameter_sensitivity()
    test_comparison_with_original()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("\n优化策略总结:")
    print("1. ✅ 语义不相似性过滤 - 避免同义词/复数")
    print("2. ✅ 词性过滤 - 仅保留名词")
    print("3. ✅ 多样性控制 - 确保结果间语义分散")
    print("4. ✅ 扰动幅度增强 - 增加语义漂移")

if __name__ == "__main__":
    main() 