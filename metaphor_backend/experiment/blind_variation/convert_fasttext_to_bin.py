#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将fastText的.vec文件转换为.bin格式，提高加载速度
"""

import os
import numpy as np
import pickle
from gensim.models import KeyedVectors

def convert_fasttext_to_bin(max_vocab=50000):
    """将fastText .vec文件转换为.bin格式"""
    print("开始转换fastText .vec文件为.bin格式...")
    
    # 文件路径
    vec_file = "data/wiki-news-300d-1M.vec"
    bin_file = "data/wiki-news-300d-1M.bin"
    
    if not os.path.exists(vec_file):
        print(f"错误：找不到文件 {vec_file}")
        return None
    
    print(f"正在加载.vec文件: {vec_file}")
    print(f"限制词汇量: {max_vocab}")
    
    try:
        # 加载.vec文件，限制词汇量
        word_vectors = KeyedVectors.load_word2vec_format(vec_file, binary=False, limit=max_vocab)
        
        print(f"加载完成，词汇量: {len(word_vectors)}")
        
        # 保存为.bin格式
        print(f"正在保存为.bin格式: {bin_file}")
        word_vectors.save(bin_file)
        
        print(f"转换完成！")
        print(f"  .vec文件大小: {os.path.getsize(vec_file) / (1024*1024):.1f} MB")
        print(f"  .bin文件大小: {os.path.getsize(bin_file) / (1024*1024):.1f} MB")
        
        return bin_file
        
    except Exception as e:
        print(f"转换失败: {e}")
        return None

def create_optimized_cache_from_vec(max_vocab=50000):
    """直接从.vec文件创建优化的缓存文件"""
    print("\n直接从.vec文件创建优化的缓存文件...")
    
    # 文件路径
    vec_file = "data/wiki-news-300d-1M.vec"
    cache_file = "data/fasttext_cache.pkl"
    
    if not os.path.exists(vec_file):
        print(f"错误：找不到文件 {vec_file}")
        return None
    
    try:
        # 直接从.vec文件加载，限制词汇量
        print(f"正在加载.vec文件: {vec_file}")
        word_vectors = KeyedVectors.load_word2vec_format(vec_file, binary=False, limit=max_vocab)
        
        # 转换为numpy格式
        word_to_idx = {}
        embeddings = []
        idx_to_word = {}
        
        vocab_list = list(word_vectors.key_to_index.keys())
        print(f"正在处理 {len(vocab_list)} 个词汇...")
        
        for idx, word in enumerate(vocab_list):
            word_to_idx[word] = idx
            vector = word_vectors[word]
            embeddings.append(vector)
            idx_to_word[idx] = word
        
        embeddings = np.array(embeddings)
        
        # 保存缓存
        cache_data = {
            'word_to_idx': word_to_idx,
            'embeddings': embeddings,
            'idx_to_word': idx_to_word
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        
        print(f"缓存文件创建完成: {cache_file}")
        print(f"  词汇量: {len(word_to_idx)}")
        print(f"  向量维度: {embeddings.shape[1]}")
        print(f"  缓存文件大小: {os.path.getsize(cache_file) / (1024*1024):.1f} MB")
        
        return cache_file
        
    except Exception as e:
        print(f"创建缓存失败: {e}")
        return None

def create_optimized_cache_from_bin(max_vocab=50000):
    """从.bin文件创建优化的缓存文件"""
    print("\n从.bin文件创建优化的缓存文件...")
    
    # 文件路径
    bin_file = "data/wiki-news-300d-1M.bin"
    cache_file = "data/fasttext_cache.pkl"
    
    if not os.path.exists(bin_file):
        print(f"错误：找不到文件 {bin_file}")
        return None
    
    try:
        # 加载.bin文件
        print(f"正在加载.bin文件: {bin_file}")
        word_vectors = KeyedVectors.load(bin_file)
        
        # 转换为numpy格式并限制词汇量
        word_to_idx = {}
        embeddings = []
        idx_to_word = {}
        
        vocab_list = list(word_vectors.key_to_index.keys())[:max_vocab]
        
        print(f"正在处理前 {len(vocab_list)} 个词汇...")
        
        for idx, word in enumerate(vocab_list):
            word_to_idx[word] = idx
            vector = word_vectors[word]
            embeddings.append(vector)
            idx_to_word[idx] = word
        
        embeddings = np.array(embeddings)
        
        # 保存缓存
        cache_data = {
            'word_to_idx': word_to_idx,
            'embeddings': embeddings,
            'idx_to_word': idx_to_word
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        
        print(f"缓存文件创建完成: {cache_file}")
        print(f"  词汇量: {len(word_to_idx)}")
        print(f"  向量维度: {embeddings.shape[1]}")
        print(f"  缓存文件大小: {os.path.getsize(cache_file) / (1024*1024):.1f} MB")
        
        return cache_file
        
    except Exception as e:
        print(f"创建缓存失败: {e}")
        return None

def test_loading_speed():
    """测试加载速度"""
    print("\n=== 加载速度测试 ===")
    
    import time
    
    # 测试.vec文件加载速度（限制词汇量）
    if os.path.exists("data/wiki-news-300d-1M.vec"):
        print("测试.vec文件加载速度（限制50000词汇）...")
        start_time = time.time()
        try:
            word_vectors = KeyedVectors.load_word2vec_format("data/wiki-news-300d-1M.vec", binary=False, limit=50000)
            vec_time = time.time() - start_time
            print(f"  .vec文件加载时间: {vec_time:.2f} 秒")
            print(f"  词汇量: {len(word_vectors)}")
        except Exception as e:
            print(f"  .vec文件加载失败: {e}")
    
    # 测试.bin文件加载速度
    if os.path.exists("data/wiki-news-300d-1M.bin"):
        print("测试.bin文件加载速度...")
        start_time = time.time()
        try:
            word_vectors = KeyedVectors.load("data/wiki-news-300d-1M.bin")
            bin_time = time.time() - start_time
            print(f"  .bin文件加载时间: {bin_time:.2f} 秒")
            print(f"  词汇量: {len(word_vectors)}")
        except Exception as e:
            print(f"  .bin文件加载失败: {e}")
    
    # 测试缓存文件加载速度
    if os.path.exists("data/fasttext_cache.pkl"):
        print("测试缓存文件加载速度...")
        start_time = time.time()
        try:
            with open("data/fasttext_cache.pkl", 'rb') as f:
                cache_data = pickle.load(f)
            cache_time = time.time() - start_time
            print(f"  缓存文件加载时间: {cache_time:.2f} 秒")
            print(f"  词汇量: {len(cache_data['word_to_idx'])}")
        except Exception as e:
            print(f"  缓存文件加载失败: {e}")

def main():
    """主函数"""
    print("fastText文件格式转换工具")
    print("=" * 50)
    
    # 检查现有文件
    print("检查现有文件:")
    files_to_check = [
        "data/wiki-news-300d-1M.vec",
        "data/wiki-news-300d-1M.bin", 
        "data/fasttext_cache.pkl"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024*1024)
            print(f"  ✓ {file_path}: {size_mb:.1f} MB")
        else:
            print(f"  ✗ {file_path}: 不存在")
    
    print("\n选择转换方式:")
    print("1. 转换为.bin格式（需要更多内存）")
    print("2. 直接创建缓存文件（推荐）")
    print("3. 从.bin文件创建缓存文件")
    
    choice = input("请选择 (1/2/3): ").strip()
    
    if choice == "1":
        # 1. 转换为.bin格式
        bin_file = convert_fasttext_to_bin(max_vocab=50000)
        if bin_file:
            # 2. 创建优化缓存
            cache_file = create_optimized_cache_from_bin()
    elif choice == "2":
        # 直接创建缓存文件
        cache_file = create_optimized_cache_from_vec(max_vocab=50000)
    elif choice == "3":
        # 从.bin文件创建缓存文件
        cache_file = create_optimized_cache_from_bin(max_vocab=50000)
    else:
        print("无效选择")
        return
    
    # 测试加载速度
    test_loading_speed()
    
    print("\n" + "=" * 50)
    print("转换完成！")
    print("现在可以使用更快的.bin文件或缓存文件了。")

if __name__ == "__main__":
    main() 