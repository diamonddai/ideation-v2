from typing import Dict, Any, List

def build_prompt0_v5(input_data: Dict[str, Any]) -> str:
    """
    基于v5中文指导原则构建prompt0
    
    v5原则强调：
    - 隐喻为结构，数据表达趋势即可，装饰最少
    - 输出概念性视觉线稿（约30%完成度）
    - 给设计师保留70%的延展空间
    - 去数值、保关系，突出变量间的相对关系与趋势
    - 无坐标轴设计，以隐喻结构承载信息
    """
    
    keyword = input_data.get("keyword", "")
    data_fact = input_data.get("dataFact", "")
    context_description = input_data.get("contextDescription", "")
    default_plan = input_data.get("defaultPlan", "")
    
    # 直接使用中文原则
    fixed_requirements = """
本版强调"隐喻为结构，数据表达趋势即可，装饰最少"。输出定位为概念性视觉线稿（约30%完成度），给设计师保留70%的延展空间。

一、目标与完成度
- 使用[metaphor_vehicle]作为整体结构来编码[data_tenor]；传达趋势（而非精确数值）
- 产出概念草图（约30%完成度）：保留清晰的隐喻结构与数据映射关系，不追求像素级细节
- 去数值、保关系：避免具体数值渲染，突出变量间的相对关系与趋势
- 无坐标轴设计（negative: no axes, no ticks, no gridlines）

二、设计优先级与权重
- 优先级：隐喻载体 > 数据映射 >> 装饰细节
- 视觉权重建议：隐喻结构承载信息，避免装饰性元素

三、信息维度与留白
- 视觉映射通道严格根据输入数据来确定，不要自己创造通道
- 移除装饰性背景纹理，保留充足留白以增强可读性与层次感
- 无坐标轴布局：以隐喻结构承载信息；禁止：no axes, no ticks, no gridlines；如需对齐，仅允许极淡的对齐点/极短虚线（不得形成网格或坐标感）

四、映射规则与可读性
- 一对一：一种数据维度对应一种视觉通道，避免复用与歧义
- 明示映射：以自然语言注释的方式写清"数据字段 → 视觉通道"，并嵌入隐喻主体
- 空间逻辑：时间/顺序优先用位置通道编码，强化阅读路径
- 映射需写作注释并直接嵌入隐喻主体，不得以坐标轴/刻度形式表现

五、版式与层次
- 建立前景/中景/背景的清晰结构，避免要素堆叠与相互遮挡
- 使用矢量几何元素，构图极简、边缘清晰

六、色彩与文字
- 文字最小化：避免大段文本与密集标签，仅保留必要注释
- 背景用纯白色

七、隐喻即结构（弱化坐标轴）
- 不描述"像图表/像可视化"，而是"使用某隐喻作为整体结构编码数据"
- 优先用自然布局替代坐标轴，例如：
  - arranged as concentric rings like tree rings
  - displayed as a flowing hourglass shape
  - scattered across a field of poppies

八、禁忌与反例
- 禁止层层堆叠导致对应关系不清
- 禁止与数据无关的装饰元素、纹理、复杂背景
- 禁止写实风格与摄影质感
- 禁止信息图（主体附近有过多冗余解释）

九、数据事实融入
- 依据数据事实选用可控的动态词：rising / shrinking / oscillating / steady / spiking 等
- 只需要能反应大致趋势即可

十、风格锚点
- 使用一致的风格锚点以稳态输出：clean vector graphics, abstract minimalism, sketch，balanced composition, subtle metaphorical elegance

十一、视觉通道示例化表达
- each flower represents one victim, petal color = category, size = age
- each ring in the tree cross-section = one decade, thickness = population growth
"""

    # 组装完整的prompt0
    prompt0 = f"""
Input Data:
- Keyword: {keyword}
- Data Fact: {data_fact}
- Context Description: {context_description}
- Default Plan: {default_plan}

{fixed_requirements}

Task: Generate a detailed prompt1 for text-to-image generation that follows these principles exactly.
"""

    return prompt0.strip()


def get_v5_metadata() -> Dict[str, str]:
    """获取v5版本的元数据"""
    return {
        "version": "v5",
        "description": "隐喻为结构，数据表达趋势即可，装饰最少 - 概念性视觉线稿（30%完成度）",
        "key_features": [
            "axes-less layout",
            "conceptual sketch (30% completion)",
            "metaphor as structure",
            "trend over exact values",
            "minimal decoration"
        ]
    }
