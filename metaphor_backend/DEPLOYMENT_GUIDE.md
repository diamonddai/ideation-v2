# Metaphor Backend 部署指南

## 📦 项目压缩包信息

- **文件名**: `metaphor_backend.tar.gz`
- **大小**: 57MB
- **位置**: `/home/dzc/Ideation/metaphor_backend.tar.gz`

## 🚀 本地Mac部署步骤

### 1. 下载和解压

```bash
# 下载压缩包到本地Mac
# 解压到目标目录
tar -xzf metaphor_backend.tar.gz
cd metaphor_backend
```

### 2. 环境准备

```bash
# 创建虚拟环境（推荐）
python3 -m venv metaphor_env
source metaphor_env/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装实验模块依赖
pip install -r experiment/blind_variation/requirements_experiment.txt
```

### 3. 环境配置

创建 `.env` 文件：
```bash
# 必需配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://ai-yyds.com/v1

# 可选配置
HOST=127.0.0.1
PORT=8000
DEBUG=True
LOG_LEVEL=INFO
```

### 4. 启动服务

```bash
# 实验室环境启动（推荐）
python start_lab.py

# 或者直接启动
python main.py
```

### 5. 测试API

```bash
# 测试健康检查
curl http://127.0.0.1:8000/health

# 测试Blind Variation API
curl -X POST "http://127.0.0.1:8000/api/v1/module2/generate/blind" \
  -H "Content-Type: application/json" \
  -d '{"boundField": {"field": "ocean", "dataFact": "growth"}}'
```

## 🔧 核心功能

### Blind Variation API (V4集成)

**端点**: `POST /api/v1/module2/generate/blind`

**输入格式**:
```json
{
  "boundField": {
    "field": "ocean",
    "dataFact": "growth"
  }
}
```

**输出格式**:
```json
{
  "variations": [
    {
      "field": "ocean",
      "keyword": "sea",
      "dataFact": "growth",
      "method": 0,
      "score": 0.5840
    }
  ]
}
```

### 算法特性

- ✅ **FastText词向量**: 50,000词汇，300维向量
- ✅ **三层向量漂移突变机制**: 基因突变、生态位探索、适应性辐射
- ✅ **保底机制**: 确保至少3个结果
- ✅ **质量过滤**: 名词过滤、形态相似性检查、隐喻友好性
- ✅ **高性能**: 平均0.1秒响应时间

## 📁 项目结构

```
metaphor_backend/
├── agents/                          # 多Agent模块
│   ├── module1_data_understanding/  # 数据理解模块
│   ├── module2_metaphor_generation/ # 隐喻生成模块
│   └── module3_visualization_generation/ # 可视化生成模块
├── experiment/                      # 实验模块
│   └── blind_variation/            # Blind Variation算法
│       ├── blind_variation_v4.py   # V4优化版算法
│       ├── data/fasttext_cache.pkl # FastText词向量缓存
│       └── README_blind_variation.md # 算法文档
├── main.py                         # 主启动文件
├── start_lab.py                    # 实验室环境启动脚本
├── requirements.txt                # 主依赖
└── config.py                       # 配置文件
```

## 🧪 测试脚本

```bash
# 测试Blind Variation集成
python test_blind_metaphor_integration.py

# 测试API格式
python test_api_format.py

# 测试V4算法
cd experiment/blind_variation
python blind_variation_v4.py
```

## 🔗 GitHub推送

```bash
# 初始化Git仓库
git init
git add .
git commit -m "Initial commit: Metaphor Backend with V4 Blind Variation"

# 添加远程仓库
git remote add origin https://github.com/yourusername/metaphor-backend.git

# 推送代码
git push -u origin main
```

## 📝 注意事项

1. **词向量文件**: `data/fasttext_cache.pkl` (61MB) 已包含在压缩包中
2. **环境变量**: 必须配置 `OPENAI_API_KEY`
3. **端口冲突**: 默认使用8000端口，可修改 `.env` 文件
4. **依赖版本**: 建议使用Python 3.8+

## 🆘 常见问题

**Q: 启动时提示缺少依赖？**
A: 运行 `pip install -r requirements.txt`

**Q: API返回空结果？**
A: 检查输入词是否在FastText词汇表中（仅支持英文）

**Q: 词向量加载失败？**
A: 确保 `data/fasttext_cache.pkl` 文件存在且完整

**Q: 端口被占用？**
A: 修改 `.env` 文件中的 `PORT` 配置
