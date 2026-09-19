# Metaphor Generation Backend

基于表格数据生成隐喻性图像提示词的多 Agent 后端系统

## 项目结构

```
metaphor-backend/
├── agents/
│   ├── module1_data_understanding/     # 数据理解模块
│   ├── module2_metaphor_generation/    # 隐喻生成模块
│   └── module3_visualization_generation/ # 预览图生成模块
├── models/                             # Pydantic 模型
├── main.py                            # 主启动文件
├── requirements.txt                   # 项目依赖
├── README.md                          # 项目说明
└── .gitignore                         # Git 忽略文件
```

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务：
```bash
python main.py
```

3. 访问 API 文档：
```
http://localhost:8000/docs
```

## API 接口列表

### 模块一：数据理解模块 (Data Understanding)

#### 1. 表头语义分析 Agent
- **路径**: `POST /api/v1/module1/analyze/header`
- **功能**: 分析表格字段名，提取关键词和上下文描述
- **输入**: 字段名列表
- **输出**: 关键词列表 + 数据上下文描述

#### 2. 数据模式识别 Agent
- **路径**: `POST /api/v1/module1/analyze/pattern`
- **功能**: 识别数据模式和趋势
- **输入**: 表格数据样本
- **输出**: 数据模式描述 + 趋势分析

#### 3. 上下文分析 Agent
- **路径**: `POST /api/v1/module1/analyze/context`
- **功能**: 分析数据业务上下文
- **输入**: 数据描述和业务背景
- **输出**: 业务上下文分析结果

### 模块二：隐喻生成模块 (Metaphor Generation)

#### 4. 引导式隐喻生成 Agent
- **路径**: `POST /api/v1/module2/guided/generate`
- **功能**: 基于多个策略生成隐喻
- **输入**: 数据理解结果
- **输出**: 多个隐喻方案

#### 5. 盲式隐喻生成 Agent
- **路径**: `POST /api/v1/module2/blind/generate`
- **功能**: 算法计算生成隐喻
- **输入**: 数据特征
- **输出**: 算法生成的隐喻结果

### 模块三：预览图生成模块 (Visualization Generation)

#### 6. 提示词生成 Agent
- **路径**: `POST /api/v1/module3/generate/prompt`
- **功能**: 基于隐喻生成图像提示词
- **输入**: 隐喻结果
- **输出**: 图像生成提示词

#### 7. 图像预览 Agent
- **路径**: `POST /api/v1/module3/generate/preview`
- **功能**: 生成预览图像
- **输入**: 图像提示词
- **输出**: 预览图像或图像描述

## 开发说明

- 每个 Agent 都是独立的 FastAPI 路由
- 使用 Pydantic 定义输入输出模型
- 基于 LangChain 构建 Agent 逻辑
- 支持异步处理
- 包含完整的错误处理和日志记录

## 团队协作

- 每个模块独立开发
- 遵循 RESTful API 设计规范
- 使用统一的错误码和响应格式
- 支持 API 版本控制

## 环境配置

### 1. 创建环境变量文件

创建 `.env` 文件配置环境变量：

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# OpenAI 配置 - 第三方 API 中转
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.nbai.art/v1
OPENAI_MODEL_NAME=gpt-4

# LangChain 配置
LANGCHAIN_TRACING_V2=false
LANGCHAIN_ENDPOINT=
LANGCHAIN_API_KEY=
```

### 2. 第三方 API 中转配置说明

本项目支持使用第三方 API 中转服务：

- **API Base URL**: `https://ai-yyds.com/v1`
- **LangChain 调用 URL**: `https://ai-yyds.com/v1`
- **配置说明**: 使用 LangChain 时请设置环境变量 `OPENAI_API_BASE` 的 URL 为 `https://ai-yyds.com/v1`

### 3. 快速配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置您的 API Key
# 将 your_openai_api_key_here 替换为您的实际 API Key
``` 