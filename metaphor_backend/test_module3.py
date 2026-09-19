"""
测试模块三：预览图生成
"""

from agents.module3_visualization_generation import Module3Controller
from agents.module2_metaphor_generation.constants import MetaphorMethod


def test_module3():
    """测试模块三的完整流程"""
    
    # 创建模块三控制器
    controller = Module3Controller()
    
    # 测试参数
    test_params = {
        "field": "人口",
        "keyword": "膨胀的海洋",
        "data_fact": "增长",
        "method": MetaphorMethod.GUIDED,
        "context_description": "该数据呈现了城市人口在过去十年中的持续增长趋势。",
        "style_context": "极简主义图表风格"
    }
    
    print("🧪 开始测试模块三：预览图生成")
    print(f"输入参数: {test_params}")
    print("-" * 50)
    
    # 执行模块三
    result = controller.run(**test_params)
    
    print("📊 执行结果:")
    print(f"成功状态: {result['success']}")
    if result['success']:
        print(f"图片URL: {result['image_url']}")
        print(f"图像提示词: {result['image_prompt']}")
        print(f"数据事实描述: {result['data_fact_caption']}")
        print(f"映射通道: {result['mapping']}")
        print(f"本体: {result['source']}")
        print(f"喻体: {result['target']}")
    else:
        print(f"错误信息: {result['error']}")
    
    print("-" * 50)
    print("✅ 测试完成")


if __name__ == "__main__":
    test_module3() 