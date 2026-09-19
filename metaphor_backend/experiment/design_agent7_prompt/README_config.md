# Agent7 配置管理说明

## 概述
所有 Agent7 实验参数现在集中在 `config.py` 文件中管理，避免每次命令行修改。

## 配置文件位置
`metaphor_backend/experiment/design_agent7_prompt/config.py`

## 主要配置项

### Agent7 版本与行为
- `AGENT7_VERSION`: 使用的 Agent7 版本（1, 2, 3, 4）
- `AGENT7_LIMIT`: 限制处理条数（None=全部，数字=限制条数）
- `AGENT7_SKIP_IMAGE`: 是否跳过生图（True=仅生成 prompt）

### LLM 配置
- `AGENT7_LLM_MODEL`: Agent7 使用的模型（o4-mini, gpt-4o-mini 等）
- `LLM_API_BASE`: LLM API 地址
- `AGENT7_LLM_TIMEOUT`: 超时时间（秒）
- `AGENT7_LLM_RETRIES`: 重试次数
- `AGENT7_LLM_BACKOFF`: 重试间隔

### 文生图配置
- `IMAGE_MODEL`: 文生图模型（dall-e-3）
- `IMAGE_SIZE`: 图片尺寸（1024x1024）
- `IMAGE_QUALITY`: 图片质量（standard, hd）
- `IMAGE_COUNT`: 一次生成几张图（1-10）
- `IMAGE_API_BASE`: 图片 API 地址

## 使用方法

### 1. 直接修改配置文件
编辑 `config.py` 中的参数值，然后运行：
```bash
python metaphor_backend/experiment/design_agent7_prompt/scripts/run_agent7_v1.py
```

### 2. 使用预设模式
在 `run_agent7_v1.py` 中取消注释预设模式：

```python
if __name__ == '__main__':
    # 选择一种预设模式
    Agent7Presets.debug_mode()  # 调试模式
    # Agent7Presets.fast_mode()   # 快速模式
    # Agent7Presets.full_mode()   # 完整模式
    # Agent7Presets.test_mode()   # 测试模式
    
    main()
```

### 3. 预设模式说明
- **debug_mode()**: 只处理1条，跳过生图（快速测试 prompt 生成）
- **fast_mode()**: 只处理1条，生成1张图（快速测试完整流程）
- **full_mode()**: 处理全部，生成3张图（完整实验）
- **test_mode()**: 处理前3条，生成1张图（中等规模测试）

## 常用配置示例

### 调试配置
```python
AGENT7_VERSION = 4
AGENT7_LIMIT = 1
AGENT7_SKIP_IMAGE = True
AGENT7_LLM_MODEL = "o4-mini"
```

### 生产配置
```python
AGENT7_VERSION = 4
AGENT7_LIMIT = None  # 处理全部
AGENT7_SKIP_IMAGE = False
AGENT7_LLM_MODEL = "o4-mini"
IMAGE_COUNT = 3
```

## 注意事项
1. 修改配置后直接运行脚本即可，无需命令行参数
2. 配置会自动应用到环境变量
3. 如需临时覆盖，仍可使用命令行环境变量
4. 建议使用预设模式进行不同场景的测试

