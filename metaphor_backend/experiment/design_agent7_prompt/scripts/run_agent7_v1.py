import os
import json
from typing import List, Dict, Any

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 优先加载 metaphor_backend/.env（如果存在）
try:
    from dotenv import load_dotenv  # type: ignore
    _base_dir = os.path.dirname(__file__)
    _backend_env_path = os.path.abspath(os.path.join(_base_dir, '..', '..', '..', '.env'))
    if os.path.exists(_backend_env_path):
        load_dotenv(_backend_env_path)
except Exception:
    pass

# 导入配置并应用到环境变量
from experiment.design_agent7_prompt.config import Agent7Config, Agent7Presets

# 应用配置到环境变量
Agent7Config.apply_to_env()

# 打印当前配置参数
def print_config():
    """打印当前配置参数"""
    print("=" * 60)
    print("Agent7 实验配置参数")
    print("=" * 60)
    
    config_dict = Agent7Config.get_env_config()
    for key, value in config_dict.items():
        if value is not None:
            print(f"{key:25} = {value}")
    
    print("=" * 60)

print_config()

from experiment.design_agent7_prompt.agent.agent7_v1 import build_prompt1
from experiment.design_agent7_prompt.agent.agent7_v2 import build_prompt1_v2
from experiment.design_agent7_prompt.agent.agent7_v3 import build_prompt1_v3
from experiment.design_agent7_prompt.agent.agent7_v4 import build_prompt1_v4
from experiment.design_agent7_prompt.agent.agent7_v5 import create_agent7_v5
from experiment.design_agent7_prompt.prompt0.v5_prompt0_builder import build_prompt0_v5
from experiment.design_agent7_prompt.image_generation.api_generator import ApiImageGenerator


def load_input_payloads(input_dir: str) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(input_dir)):
        if not name.endswith('.json'):
            continue
        path = os.path.join(input_dir, name)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        spec = data.get('mapping_spec') or {}
        payloads.append({
            'keyword': spec.get('keyword', 'metaphor'),
            'dataFact': spec.get('dataFact', 'trend'),
            'contextDescription': spec.get('contextDescription', ''),
            'defaultPlan': spec.get('defaultPlan', []),
            '_source_file': name,
        })
    return payloads


def main() -> None:
    base_dir = os.path.dirname(__file__)
    input_dir = os.path.abspath(os.path.join(base_dir, '..', 'input_data'))
    outputs_dir = os.path.abspath(os.path.join(base_dir, '..', 'outputs'))
    os.makedirs(outputs_dir, exist_ok=True)

    items = load_input_payloads(input_dir)
    print(f"[Runner] Loaded {len(items)} input payload(s) from {input_dir}")
    # 限制处理条数（调试/加速）
    limit = os.getenv('AGENT7_LIMIT')
    if limit and limit.isdigit():
        items = items[: int(limit)]

    # 生成 Prompt1 并保存（支持跳过生成直接复用历史 prompts）
    prompt_dump_path = os.path.join(outputs_dir, 'agent7_v1_prompts.json')
    results: List[Dict[str, Any]] = []

    # 允许跳过prompt生成，直接使用之前保存的prompt
    skip_prompt_generation = os.getenv('AGENT7_SKIP_PROMPT', 'false').lower() in ('1', 'true', 'yes')
    # 无论是否跳过，先解析版本，后续文件命名会使用
    version = os.getenv('AGENT7_VERSION', '1')

    if skip_prompt_generation:
        print("[Runner] 跳过prompt生成，使用之前保存的prompt文件...")
        # 查找最新的prompt文件
        prompt_files = [f for f in os.listdir(outputs_dir) if f.endswith('_prompts.json')]
        if prompt_files:
            prompt_files.sort(key=lambda x: os.path.getmtime(os.path.join(outputs_dir, x)), reverse=True)
            latest_prompt_file = prompt_files[0]
            prompt_file_path = os.path.join(outputs_dir, latest_prompt_file)
            print(f"[Runner] 使用最新的prompt文件: {latest_prompt_file}")
            try:
                with open(prompt_file_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                print(f"[Runner] 成功加载 {len(results)} 个prompt")
            except Exception as e:
                print(f"[Runner] 加载prompt文件失败: {e}")
                return
        else:
            print("[Runner] 未找到prompt文件，无法跳过prompt生成")
            return
    else:
        use_v2 = version == '2'
        use_v3 = version == '3'
        use_v4 = version == '4'
        use_v5 = version == '5'

        # 若为 v3/v4/v5，需要读取中文原则文本作为 prompt0 的一部分
        principles_text = ""
        if use_v3 or use_v4 or use_v5:
            if use_v5:
                default_file = 'v5_principles_zh.md'
            elif use_v4:
                default_file = 'v4_principles_zh.md'
            else:
                default_file = 'v3_principles_zh.md'
            principles_path = os.getenv('AGENT7_V3_PRINCIPLES_PATH') or os.path.abspath(os.path.join(base_dir, '..', 'principles', default_file))
            try:
                with open(principles_path, 'r', encoding='utf-8') as f:
                    principles_text = f.read()
            except Exception:
                principles_text = ''

        for idx, payload in enumerate(items, 1):
            print(f"[Runner] Building prompt (version={version}) for #{idx}: keyword={payload.get('keyword')} dataFact={payload.get('dataFact')}")
            if use_v5:
                # v5使用新的Agent7架构
                agent7_v5 = create_agent7_v5()
                prompt0 = build_prompt0_v5(payload)
                prompt1 = agent7_v5.generate_prompt1(prompt0)
                if prompt1:
                    res = {
                        'prompt1': prompt1,
                        'meta': agent7_v5.get_metadata()
                    }
                else:
                    res = {
                        'prompt1': 'Error: Failed to generate prompt1',
                        'meta': agent7_v5.get_metadata()
                    }
            elif use_v4:
                res = build_prompt1_v4(payload, principles_text)
            elif use_v3:
                res = build_prompt1_v3(payload, principles_text)
            elif use_v2:
                res = build_prompt1_v2(payload)
            else:
                res = build_prompt1(payload)
            results.append({
                'index': idx,
                'source_file': payload.get('_source_file'),
                'payload': {k: payload[k] for k in ['keyword', 'dataFact', 'contextDescription', 'defaultPlan']},
                'prompt1': res['prompt1'],
                'meta': res['meta'],
            })

        with open(prompt_dump_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[Runner] Saved prompts to {prompt_dump_path}")

    # 允许跳过生图以观察 LLM 生成速度
    skip_image = os.getenv('AGENT7_SKIP_IMAGE', 'false').lower() in ('1', 'true', 'yes')

    if not skip_image:
        print("[Runner] Generating images via API...")
        generator = ApiImageGenerator(output_dir=outputs_dir)
        for item in results:
            prompt = item['prompt1']
            prefix = f"v{version}_{item['index']}_{item['payload']['keyword']}"
            # 从 meta 中获取 Agent7 模型版本
            agent7_model = item['meta'].get('llm', 'unknown')
            # 从配置获取图片生成数量
            image_count = int(os.getenv('IMAGE_COUNT', '3'))
            save_result = generator.generate_and_save(prompt, filename_prefix=prefix, agent7_model=agent7_model)
            print(json.dumps({
                'index': item['index'],
                'local_path': save_result.get('local_path'),
                'prompt_path': save_result.get('prompt_path'),
                'success': save_result.get('success'),
                'error': save_result.get('error'),
                'image_count': image_count,
            }, ensure_ascii=False))
        print("[Runner] Image generation finished.")
    else:
        print("[Runner] Skipped image generation (AGENT7_SKIP_IMAGE=true)")


if __name__ == '__main__':
    # 使用预设模式（可选）
    # Agent7Presets.debug_mode()  # 调试模式：只处理1条，跳过生图
    # Agent7Presets.fast_mode()   # 快速模式：只处理1条，生成1张图
    # Agent7Presets.full_mode()   # 完整模式：处理全部，生成3张图
    # Agent7Presets.test_mode()   # 测试模式：处理前3条，生成1张图
    
    main()


