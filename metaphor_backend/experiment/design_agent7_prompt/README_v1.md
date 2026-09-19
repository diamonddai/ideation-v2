### Agent 7 重构（V1）

目录划分：
- `principles/v1_principles_zh.md`：中文设计指导原则（V1）。
- `prompt0/v1_prompt0_builder.py`：将输入（keyword, dataFact, contextDescription, defaultPlan）+固定英文要求组装为 Prompt0。
- `agent/agent7_v1.py`：将 Prompt0 作为 Prompt1（可在此扩展为特定模型前后缀）。
- `image_generation/local_generator.py`：仅本地保存（prompt 文本与占位 PNG），不上传 OSS。
- `scripts/run_agent7_v1.py`：读取 `input_data/*.json` 的 `mapping_spec` 字段生成 Prompt1 和本地图片。
- `outputs/`：运行后输出目录。

使用方法：
1. 安装可选依赖（若想生成占位图像）：`pip install pillow`。
2. 运行：
```bash
# 本地占位图（默认）
python metaphor_backend/experiment/design_agent7_prompt/scripts/run_agent7_v1.py

# 调用文生图 API（需 OPENAI_API_KEY；可用 IMAGE_API_BASE 覆盖 api_base）
AGENT7_USE_API=true IMAGE_API_BASE="https://your-api-base" \
python metaphor_backend/experiment/design_agent7_prompt/scripts/run_agent7_v1.py
```
3. 结果：
   - `outputs/agent7_v1_prompts.json`：汇总的 Prompt1 与 meta。
   - `outputs/v1_{index}_{keyword}.png`：占位图片。
   - `outputs/v1_{index}_{keyword}_prompt.txt`：对应的 Prompt 文本。

扩展：
- 新版本仅需：
  1) 更新/新增中文指导原则。
  2) 生成对应的 Prompt0 构建器（复制并修改 `prompt0/v1_prompt0_builder.py`）。
  3) 在 `agent/` 新增对应版本的 Agent。


