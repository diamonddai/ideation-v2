"""
模块二：隐喻生成模块常量定义
"""

from enum import Enum

# 隐喻生成方法枚举
class MetaphorMethod(Enum):
    BLIND = 0   # 语义扰动发散
    GUIDED = 1  # 结构性发散

# 隐喻生成方法常量
GUIDED = 1  # 结构性发散
BLIND = 0   # 语义扰动发散

# 六类隐喻构思策略
METAPHOR_STRATEGIES = [
    "SUBSTITUTE",    # 替代
    "COMBINE",       # 合并
    "ADAPT",         # 适应
    "MODIFY",        # 修改
    "REFRAME",       # 重构
    "REVERSE"        # 颠倒
]

# 设计空间维度
DESIGN_DIMENSIONS = [
    "用途",      # how it is used
    "行为",      # how it moves
    "颜色",      # 视觉色彩特征
    "纹理",      # 表面质地特征
    "形状",      # 几何形态特征
    "结构",      # 内部组织方式
    "方向",      # 空间或时间方向
    "情绪",      # 情感色彩（积极/消极/中立）
    "语义关系",  # 因果关系/类属关系/象征关系
    "功能"       # 行为/用途
]

# 策略描述
STRATEGY_DESCRIPTIONS = {
    "SUBSTITUTE": "替代策略：用相似概念替代原概念，保持核心语义",
    "COMBINE": "合并策略：将原概念与其他概念组合，创造新的复合概念",
    "ADAPT": "适应策略：让原概念适应不同场景或环境",
    "MODIFY": "修改策略：修改原概念的属性、特征或状态",
    "REFRAME": "重构策略：重新构建概念的关系或结构",
    "REVERSE": "颠倒策略：反向思考，对立或相反的概念"
}

# 旧版 SCAMPER 发散策略（保留兼容性）
SCAMPER_STRATEGIES = [
    "SUBSTITUTE",    # 替代
    "COMBINE",       # 组合
    "ADAPT",         # 适应
    "MODIFY",        # 修改
    "PUT_TO_OTHER_USE",  # 他用
    "ELIMINATE",     # 消除
    "REVERSE"        # 反向
] 