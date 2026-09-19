# 快速启动指南

## 🚀 环境准备

### 1. 激活 conda 环境（你自己的 conda 环境）
```bash
conda activate metaphor_ai
```

### 2. 配置 API Key
编辑 `.env` 文件，设置您的 API Key：
```bash
# 将 your_openai_api_key_here 替换为您的实际 API Key
OPENAI_API_KEY=your_actual_api_key_here
```

### 3. 测试配置
```bash
python test_config.py
```

## 🏃‍♂️ 启动服务

### 方式一：使用启动脚本（推荐）
```bash
python start.py
```

### 方式二：直接启动
```bash
python main.py
```

## 📖 访问 API 文档

启动成功后，访问以下地址查看 API 文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 测试 API

### 测试表头语义分析
```bash
curl -X POST "http://localhost:8000/api/v1/module1/analyze/header" \
     -H "Content-Type: application/json" \
     -d '{
       "headers": ["用户ID", "年龄", "收入", "购买金额"]
     }'
```

## 🛠️ 故障排除

### 1. 依赖问题
```bash
# 重新安装依赖
conda install -c conda-forge fastapi uvicorn pydantic pandas numpy langchain langchain-openai langchain-community openai python-dotenv -y
```

### 2. API 连接问题
- 检查 `.env` 文件中的 API Key 是否正确
- 确认网络连接正常
- 验证第三方 API 服务是否可用

### 3. 端口占用
如果 8000 端口被占用，可以修改 `.env` 文件中的 PORT 设置：
```bash
PORT=8001
```

## 📁 项目结构
```
metaphor_backend/
├── agents/                    # Agent 模块
│   ├── module1_data_understanding/     # 数据理解模块
│   ├── module2_metaphor_generation/    # 隐喻生成模块
│   └── module3_visualization_generation/ # 预览图生成模块
├── models/                    # 数据模型
├── utils/                     # 工具类
├── main.py                   # 主启动文件
├── config.py                 # 配置文件
├── start.py                  # 启动脚本
├── test_config.py            # 配置测试
├── requirements.txt          # 依赖列表
├── .env                      # 环境变量
└── README.md                 # 项目说明
``` 