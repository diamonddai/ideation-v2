#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API输入输出格式
"""

import sys
import os
from pathlib import Path
import asyncio
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.module2_metaphor_generation.blind_metaphor_agent import (
    BlindVariationInput, 
    BoundField,
    blind_variation_agent
)

async def test_api_format():
    """测试API输入输出格式"""
    print("=== 测试API输入输出格式 ===")
    
    # 测试输入格式
    test_input = {
        "field": "ocean",
        "dataFact": "growth"
    }
    
    print(f"输入格式:")
    print(json.dumps(test_input, indent=2, ensure_ascii=False))
    
    # 转换为API输入
    api_input = BlindVariationInput(
        boundField=BoundField(
            field=test_input["field"],
            dataFact=test_input["dataFact"]
        )
    )
    
    print(f"\nAPI输入:")
    print(json.dumps(api_input.model_dump(), indent=2, ensure_ascii=False))
    
    # 调用API
    try:
        result = await blind_variation_agent(api_input)
        
        print(f"\nAPI输出:")
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        
        # 验证输出格式
        print(f"\n验证输出格式:")
        print(f"- 变体数量: {len(result.variations)}")
        print(f"- 所有变体都包含field: {all(v.field == test_input['field'] for v in result.variations)}")
        print(f"- 所有变体都包含dataFact: {all(v.dataFact == test_input['dataFact'] for v in result.variations)}")
        print(f"- 所有变体都有分数: {all(v.score is not None for v in result.variations)}")
        
        print(f"\n变体详情:")
        for i, variation in enumerate(result.variations, 1):
            print(f"  {i}. keyword: {variation.keyword}, score: {variation.score:.4f}")
            
    except Exception as e:
        print(f"API调用失败: {e}")

async def test_multiple_cases():
    """测试多个用例"""
    print("\n=== 测试多个用例 ===")
    
    test_cases = [
        {"field": "fire", "dataFact": "spread"},
        {"field": "technology", "dataFact": "development"},
        {"field": "population", "dataFact": "growth"},
        {"field": "economy", "dataFact": "recovery"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n用例 {i}: {test_case['field']} -> {test_case['dataFact']}")
        
        api_input = BlindVariationInput(
            boundField=BoundField(
                field=test_case["field"],
                dataFact=test_case["dataFact"]
            )
        )
        
        try:
            result = await blind_variation_agent(api_input)
            print(f"  生成 {len(result.variations)} 个变体:")
            for j, variation in enumerate(result.variations, 1):
                print(f"    {j}. {variation.keyword} (分数: {variation.score:.4f})")
        except Exception as e:
            print(f"  失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_format())
    asyncio.run(test_multiple_cases())
