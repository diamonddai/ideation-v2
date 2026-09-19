#!/usr/bin/env python3
"""
测试 Guided Variation 多智能体组
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.module2_metaphor_generation.guided_metaphor_agent import (
    GuidedVariationOrchestrator,
    StrategyAgent,
    MetaphorStrategy,
    BoundField,
    GuidedVariationInput
)

async def test_single_strategy():
    """测试单个策略Agent"""
    print("🧪 测试单个策略Agent...")
    
    # 创建替代策略Agent
    agent = StrategyAgent(MetaphorStrategy.SUBSTITUTE)
    
    # 测试维度选择
    keyword = "education"
    dimensions = await agent.select_dimensions(keyword)
    print(f"选择维度: {dimensions}")
    
    # 测试隐喻生成
    metaphors = await agent.generate_metaphors(keyword, dimensions)
    print(f"生成隐喻: {metaphors}")
    
    return True

async def test_all_strategies():
    """测试所有策略Agent"""
    print("🧪 测试所有策略Agent...")
    
    # 创建编排器
    orchestrator = GuidedVariationOrchestrator()
    
    # 测试关键词
    keyword = "education"
    
    # 运行所有策略
    variations = await orchestrator.run_all_strategies(keyword)
    
    print(f"总生成变体数: {len(variations)}")
    print(f"策略数量: {len(orchestrator.strategy_agents)}")
    
    # 按策略分组显示结果
    strategy_results = {}
    for variation in variations:
        strategy = variation.strategy
        if strategy not in strategy_results:
            strategy_results[strategy] = []
        strategy_results[strategy].append(variation.keyword)
    
    for strategy, keywords in strategy_results.items():
        print(f"\n{strategy}策略 ({len(keywords)}个):")
        for keyword in keywords[:3]:  # 只显示前3个
            print(f"  - {keyword}")
    
    return len(variations) > 0

async def test_api_interface():
    """测试API接口"""
    print("🧪 测试API接口...")
    
    # 创建输入数据
    input_data = GuidedVariationInput(
        boundField=BoundField(
            field="education_level",
            dataFact="高等教育普及率逐年上升"
        ),
        keyword="education"
    )
    
    # 创建编排器
    orchestrator = GuidedVariationOrchestrator()
    
    # 运行所有策略
    variations = await orchestrator.run_all_strategies(input_data.keyword)
    
    # 填充字段信息
    for variation in variations:
        variation.field = input_data.boundField.field
        variation.dataFact = input_data.boundField.dataFact
    
    print(f"API接口测试成功，生成 {len(variations)} 个变体")
    
    # 显示示例结果
    if variations:
        sample = variations[0]
        print(f"示例变体:")
        print(f"  - 字段: {sample.field}")
        print(f"  - 关键词: {sample.keyword}")
        print(f"  - 数据特征: {sample.dataFact}")
        print(f"  - 策略: {sample.strategy}")
        print(f"  - 维度: {sample.dimensions}")
        print(f"  - 原关键词: {sample.original_keyword}")
    
    return len(variations) > 0

async def main():
    """主测试函数"""
    print("🚀 开始测试 Guided Variation 多智能体组")
    print("=" * 50)
    
    try:
        # 测试1: 单个策略Agent
        print("\n1. 测试单个策略Agent")
        result1 = await test_single_strategy()
        print(f"✅ 单个策略测试: {'通过' if result1 else '失败'}")
        
        # 测试2: 所有策略Agent
        print("\n2. 测试所有策略Agent")
        result2 = await test_all_strategies()
        print(f"✅ 所有策略测试: {'通过' if result2 else '失败'}")
        
        # 测试3: API接口
        print("\n3. 测试API接口")
        result3 = await test_api_interface()
        print(f"✅ API接口测试: {'通过' if result3 else '失败'}")
        
        print("\n" + "=" * 50)
        if all([result1, result2, result3]):
            print("🎉 所有测试通过！Guided Variation 多智能体组实现成功")
        else:
            print("❌ 部分测试失败，请检查实现")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

