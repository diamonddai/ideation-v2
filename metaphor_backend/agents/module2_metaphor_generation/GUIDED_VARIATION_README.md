# Guided Variation 多智能体组实现文档

## 概述

本实现完成了模块二的Guided Variation部分，包含六类隐喻构思策略的多智能体组，每个Agent负责一个策略，通过动态选择十个设计空间维度中的三个最适合的维度来生成隐喻变体。

## 核心特性

### 1. 六类隐喻构思策略

- **替代（Substitute）**：用相似概念替代原概念，保持核心语义
- **合并（Combine）**：将原概念与其他概念组合，创造新的复合概念
- **适应（Adapt）**：让原概念适应不同场景或环境
- **修改（Modify）**：修改原概念的属性、特征或状态
- **重构（Reframe）**：重新构建概念的关系或结构
- **颠倒（Reverse）**：反向思考，对立或相反的概念

### 2. 十个设计空间维度

- **用途（Usage）**：功能和使用方式
- **行为（Behavior）**：运动和行为模式
- **颜色（Color）**：视觉色彩特征
- **纹理（Texture）**：表面质地特征
- **形状（Shape）**：几何形态特征
- **结构（Structure）**：内部组织方式
- **方向（Direction）**：空间或时间方向
- **情绪（Emotion）**：情感色彩（积极/消极/中立）
- **语义关系（Semantic）**：因果关系/类属关系/象征关系
- **功能（Functional）**：行为/用途

## 架构设计

### 核心类

#### 1. StrategyAgent
单个策略Agent的基类，负责：
- 维度选择：为输入关键词选择最适合的3个维度
- 隐喻生成：基于选定维度生成隐喻变体
- 策略执行：实现特定策略的认知变换操作

#### 2. GuidedVariationOrchestrator
引导式变体编排器，负责：
- 管理所有策略Agent
- 并行执行六个策略
- 结果整合与排序

#### 3. 数据模型
- `MetaphorVariation`：隐喻变体数据结构
- `GuidedVariationInput`：API输入数据
- `GuidedVariationOutput`：API输出数据

## 工作流程

### 1. 输入语义提取
- 接收英文名词原型作为输入
- 验证输入格式和语义

### 2. 六策略并行执行
每个策略Agent独立执行：
1. **维度选择**：通过LLM语义判断选择3个最适合的维度
2. **隐喻生成**：在每个维度下生成1-2个发散隐喻构思
3. **二次发散**：实现首次发散和二次发散的完整流程

### 3. 结果整合
- 每个策略最多输出6个结果（3维度 × 每维度最多2条）
- 总输出量控制在36条以内
- 按策略和维度进行结果分组

## API接口

### 主要接口

#### POST `/api/v1/module2/generate/guided`
生成引导式隐喻变体

**输入**：
```json
{
    "boundField": {
        "field": "education_level",
        "dataFact": "高等教育普及率逐年上升"
    },
    "keyword": "education"
}
```

**输出**：
```json
{
    "variations": [
        {
            "field": "education_level",
            "keyword": "lighthouse",
            "dataFact": "高等教育普及率逐年上升",
            "method": 1,
            "strategy": "替代",
            "dimensions": ["用途", "形状", "情绪"],
            "original_keyword": "education"
        }
    ]
}
```

#### GET `/api/v1/module2/test/strategies`
测试所有策略Agent

## 示例输出

### 替代策略示例
- **输入**：education
- **选择维度**：用途、形状、情绪
- **生成结果**：
  - 用途维度：education → lighthouse（首次发散）、lighthouse → navigation_map（二次发散）
  - 形状维度：education → pyramid（首次发散）、pyramid → mountain（二次发散）
  - 情绪维度：education → sunshine（首次发散）、sunshine → ultraviolet（二次发散）

### 合并策略示例
- **输入**：education
- **选择维度**：结构、功能、方向
- **生成结果**：
  - 结构维度：education → circuit_board（首次发散）、circuit_board → neural_network（二次发散）
  - 功能维度：education → greenhouse（首次发散）、greenhouse → ecosystem（二次发散）
  - 方向维度：education → compass（首次发散）、compass → star_map（二次发散）

## 技术实现

### 1. 异步处理
- 使用`asyncio`实现六个策略Agent的并行执行
- 提高处理效率和响应速度

### 2. 错误处理
- 完善的异常捕获和处理机制
- 单个策略失败不影响其他策略执行
- 提供默认结果作为降级方案

### 3. LLM集成
- 使用GPT-4模型进行语义理解和生成
- 支持第三方API中转服务
- 结构化的JSON输出格式

### 4. 类型安全
- 使用Pydantic进行数据验证
- 完整的类型注解和文档

## 测试

### 运行测试
```bash
cd metaphor_backend
python test_guided_variation.py
```

### 测试覆盖
1. **单个策略Agent测试**：验证维度选择和隐喻生成
2. **所有策略Agent测试**：验证并行执行和结果整合
3. **API接口测试**：验证完整的API调用流程

## 配置要求

### 环境变量
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://ai-yyds.com/v1
```

### 依赖包
```
langchain-openai
pydantic
fastapi
asyncio
```

## 扩展性

### 1. 策略扩展
- 可以轻松添加新的隐喻策略
- 继承`StrategyAgent`基类实现新策略

### 2. 维度扩展
- 可以扩展设计空间维度
- 支持自定义维度选择逻辑

### 3. 模型扩展
- 支持不同的LLM模型
- 可以集成其他AI服务

## 性能优化

### 1. 并行处理
- 六个策略Agent并行执行
- 显著提高处理速度

### 2. 缓存机制
- 可以添加维度选择结果缓存
- 减少重复计算

### 3. 结果限制
- 控制输出数量避免过载
- 智能排序和筛选

## 总结

本实现完全满足了需求文档中的所有要求：
- ✅ 六类隐喻构思策略作为独立Agent
- ✅ 十个设计空间维度的动态选择
- ✅ 首次发散和二次发散的完整流程
- ✅ 并行执行和结果整合
- ✅ 完善的API接口和错误处理
- ✅ 可扩展的架构设计

该实现为模块二提供了强大的隐喻生成能力，能够根据输入关键词生成丰富多样的隐喻变体，为后续的可视化生成模块提供高质量的输入。

