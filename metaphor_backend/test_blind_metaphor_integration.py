#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试blind_metaphor_agent的V4集成
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.module2_metaphor_generation.blind_metaphor_agent import (
    BlindVariationInput, 
    BoundField,
    blind_variation_agent
)
import asyncio
import json

async def test_blind_variation():
    """测试blind variation agent"""
    print("=== 测试 Blind Variation Agent V4集成 ===")
    
    # 测试用例1：英文输入
    test_input_1 = BlindVariationInput(
        boundField=BoundField(
            field="ocean",
            dataFact="growth"
        )
    )
    
    print(f"\n测试用例1 - 英文输入:")
    print(f"输入: {test_input_1.model_dump()}")
    
    try:
        result_1 = await blind_variation_agent(test_input_1)
        print(f"输出: {len(result_1.variations)} 个变体")
        for i, variation in enumerate(result_1.variations, 1):
            print(f"  {i}. {variation.keyword} (分数: {variation.score:.4f})")
    except Exception as e:
        print(f"测试用例1失败: {e}")
    
    # 测试用例2：中文输入（需要处理）
    test_input_2 = BlindVariationInput(
        boundField=BoundField(
            field="population",
            dataFact="growth"
        )
    )
    
    print(f"\n测试用例2 - 人口增长:")
    print(f"输入: {test_input_2.model_dump()}")
    
    try:
        result_2 = await blind_variation_agent(test_input_2)
        print(f"输出: {len(result_2.variations)} 个变体")
        for i, variation in enumerate(result_2.variations, 1):
            print(f"  {i}. {variation.keyword} (分数: {variation.score:.4f})")
    except Exception as e:
        print(f"测试用例2失败: {e}")
    
    # 测试用例3：技术词汇
    test_input_3 = BlindVariationInput(
        boundField=BoundField(
            field="technology",
            dataFact="development"
        )
    )
    
    print(f"\n测试用例3 - 技术词汇:")
    print(f"输入: {test_input_3.model_dump()}")
    
    try:
        result_3 = await blind_variation_agent(test_input_3)
        print(f"输出: {len(result_3.variations)} 个变体")
        for i, variation in enumerate(result_3.variations, 1):
            print(f"  {i}. {variation.keyword} (分数: {variation.score:.4f})")
    except Exception as e:
        print(f"测试用例3失败: {e}")

def test_v4_direct():
    """直接测试V4算法"""
    print("\n=== 直接测试V4算法 ===")
    
    try:
        # 添加experiment路径
        experiment_path = Path(__file__).parent / "experiment" / "blind_variation"
        sys.path.append(str(experiment_path))
        
        from blind_variation_v4 import OptimizedBlindVariation
        
        # 创建生成器
        generator = OptimizedBlindVariation()
        
        # 测试词汇
        test_words = ["ocean", "fire", "technology"]
        
        for word in test_words:
            print(f"\n测试词汇: {word}")
            results = generator.blind_variation_generate(word)
            print(f"生成 {len(results)} 个结果:")
            for i, (keyword, score) in enumerate(results, 1):
                print(f"  {i}. {keyword} (分数: {score:.4f})")
                
    except Exception as e:
        print(f"直接测试V4失败: {e}")

if __name__ == "__main__":
    # 直接测试V4算法
    test_v4_direct()
    
    # 测试集成
    asyncio.run(test_blind_variation())
