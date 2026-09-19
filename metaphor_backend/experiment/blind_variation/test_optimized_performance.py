#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版Blind Variation算法测试
调整参数以达到更好的发散效果
"""

import time
import os
from blind_variation import BlindVariationGenerator

def test_optimized_performance():
    """测试优化后的算法性能"""
    print("=== 优化版Blind Variation算法测试 ===")
    
    if not os.path.exists("data/fasttext_cache.pkl"):
        print("缓存文件不存在")
        return
    
    # 优化参数配置
    optimized_params = {
        'beta': 8.0,           # 降低自适应突变率参数，减少过度过滤
        'rho_0': 0.5,          # 提高密度阈值，增加发散
        'sigma_0': 0.15,       # 增加基础突变幅度
        'delta': 0.8,          # 大幅增加语义漂移幅度
        'alpha': 0.8,          # 更偏重新颖性
        'gamma': 0.1,          # 降低数据事实相关性权重
        'k': 15,               # 减少k-NN邻居数，提高计算效率
        'num_candidates': 150, # 增加候选词数量
        'top_k': 8,            # 增加返回词数量
        
        # 放宽过滤条件
        'similarity_threshold': 0.85,  # 提高相似度阈值，减少过滤
        'diversity_threshold': 0.6,    # 降低多样性阈值
        'min_similarity': 0.2,         # 降低最小相似度阈值
    }
    
    print("使用优化参数配置:")
    for key, value in optimized_params.items():
        print("  {}: {}".format(key, value))
    
    print("\n正在加载词向量模型...")
    generator = BlindVariationGenerator(embeddings_path="data/fasttext_cache.pkl", params=optimized_params)
    
    print("词向量模型信息:")
    print("  词汇量: {}".format(len(generator.word_to_idx)))
    print("  向量维度: {}".format(generator.embeddings.shape[1]))
    
    # 测试词汇列表
    test_words = ["ocean", "mountain", "fire", "wind", "city", "computer", "technology", "data", "analysis"]
    
    total_results = 0
    total_time = 0
    
    for word in test_words:
        if word in generator.word_to_idx:
            print("\n" + "=" * 50)
            print("测试词汇: {}".format(word))
            print("=" * 50)
            
            start_time = time.time()
            results = generator.blind_variation_generate(word)
            end_time = time.time()
            
            calc_time = end_time - start_time
            total_time += calc_time
            
            print("计算时间: {:.3f} 秒".format(calc_time))
            print("结果数量: {}".format(len(results)))
            total_results += len(results)
            
            if results:
                print("发散结果:")
                for i, (result_word, fitness) in enumerate(results, 1):
                    print("  {:2d}. {:15s} (适应度: {:.4f})".format(i, result_word, fitness))
                    
                    # 分析发散效果
                    if i <= 3:  # 只分析前3个结果
                        # 简单的发散效果评估
                        if result_word.lower() != word.lower() and not result_word.lower().startswith(word.lower()):
                            print("       ✓ 良好的语义发散")
                        else:
                            print("       ⚠ 语义发散不足")
            else:
                print("  没有找到合适的结果")
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print("=" * 50)
    print("总测试词汇数: {}".format(len([w for w in test_words if w in generator.word_to_idx])))
    print("总结果数量: {}".format(total_results))
    print("平均每个词汇结果数: {:.1f}".format(total_results/len([w for w in test_words if w in generator.word_to_idx])))
    print("总计算时间: {:.3f} 秒".format(total_time))
    print("平均每个词汇计算时间: {:.3f} 秒".format(total_time/len([w for w in test_words if w in generator.word_to_idx])))
    
    # 评估是否达到README要求
    avg_results = total_results / len([w for w in test_words if w in generator.word_to_idx])
    if avg_results >= 3:
        print("✓ 达到README要求：平均每个关键词 {:.1f} 个结果 (要求3-5个)".format(avg_results))
    else:
        print("✗ 未达到README要求：平均每个关键词 {:.1f} 个结果 (要求3-5个)".format(avg_results))

def test_parameter_comparison():
    """测试不同参数设置的效果对比"""
    print("\n=== 参数设置效果对比 ===")
    
    test_word = "ocean"
    
    # 原始参数
    original_params = {
        'similarity_threshold': 0.8,
        'diversity_threshold': 0.7,
        'delta': 0.6,
        'num_candidates': 100,
        'top_k': 5,
    }
    
    # 优化参数
    optimized_params = {
        'similarity_threshold': 0.85,
        'diversity_threshold': 0.6,
        'delta': 0.8,
        'num_candidates': 150,
        'top_k': 8,
    }
    
    print("测试词汇: {}".format(test_word))
    
    # 测试原始参数
    print("\n原始参数设置:")
    generator_orig = BlindVariationGenerator(embeddings_path="data/fasttext_cache.pkl", params=original_params)
    start_time = time.time()
    results_orig = generator_orig.blind_variation_generate(test_word)
    orig_time = time.time() - start_time
    
    print("  结果数量: {}".format(len(results_orig)))
    print("  计算时间: {:.3f} 秒".format(orig_time))
    if results_orig:
        print("  前3个结果:")
        for i, (word, fitness) in enumerate(results_orig[:3], 1):
            print("    {}. {:15s} (适应度: {:.4f})".format(i, word, fitness))
    
    # 测试优化参数
    print("\n优化参数设置:")
    generator_opt = BlindVariationGenerator(embeddings_path="data/fasttext_cache.pkl", params=optimized_params)
    start_time = time.time()
    results_opt = generator_opt.blind_variation_generate(test_word)
    opt_time = time.time() - start_time
    
    print("  结果数量: {}".format(len(results_opt)))
    print("  计算时间: {:.3f} 秒".format(opt_time))
    if results_opt:
        print("  前3个结果:")
        for i, (word, fitness) in enumerate(results_opt[:3], 1):
            print("    {}. {:15s} (适应度: {:.4f})".format(i, word, fitness))
    
    # 对比分析
    print("\n对比分析:")
    print("  结果数量改进: {} vs {} (+{})".format(len(results_opt), len(results_orig), len(results_opt)-len(results_orig)))
    # 百分比格式化分两步，避免 f-string
    pct = (orig_time - opt_time) / orig_time * 100 if orig_time != 0 else 0.0
    sign = "+" if pct >= 0 else ""
    print("  计算时间改进: {:.3f}s vs {:.3f}s ({}{:,.1f}%)".format(opt_time, orig_time, sign, pct))

def main():
    """主函数"""
    print("=== Blind Variation 算法优化测试 ===")
    print("目标：达到README要求 - 每个关键词3-5个发散结果")
    print("=" * 60)
    
    # 检查文件状态
    print("检查文件状态:")
    if os.path.exists("data/fasttext_cache.pkl"):
        size_mb = os.path.getsize("data/fasttext_cache.pkl") / (1024 * 1024)
        print("  ✓ data/fasttext_cache.pkl: {:.1f} MB".format(size_mb))
    else:
        print("  ✗ data/fasttext_cache.pkl: 不存在")
        return
    
    # 运行测试
    test_optimized_performance()
    test_parameter_comparison()
    
    print("\n" + "=" * 60)
    print("优化建议:")
    print("1. 增加语义漂移幅度 (delta: 0.6 → 0.8)")
    print("2. 放宽相似度过滤条件 (similarity_threshold: 0.8 → 0.85)")
    print("3. 增加候选词数量 (num_candidates: 100 → 150)")
    print("4. 提高新颖性权重 (alpha: 0.7 → 0.8)")
    print("5. 降低多样性阈值 (diversity_threshold: 0.7 → 0.6)")

if __name__ == "__main__":
    main()
