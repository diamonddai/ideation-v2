import os
import json
from typing import List, Dict, Any

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from experiment.design_agent7_prompt.agent.agent7_v1 import build_prompt1


def sample_inputs() -> List[Dict[str, Any]]:
    return [
        {
            "keyword": "expanding ocean waves",
            "dataFact": "增长",
            "contextDescription": "该数据呈现了城市人口在过去十年中的持续增长趋势",
            "defaultPlan": [
                {"dataField": "时间", "subitemId": "wave_line", "channels": ["position"]},
                {"dataField": "人口", "subitemId": "wave_band", "channels": ["size"]},
            ],
        },
        {
            "keyword": "shrinking mountain ridges",
            "dataFact": "下降",
            "contextDescription": "某地区工业产出逐年下滑",
            "defaultPlan": [
                {"dataField": "年份", "subitemId": "ridge_line", "channels": ["position"]},
                {"dataField": "产出", "subitemId": "ridge_band", "channels": ["size"]},
            ],
        },
        {
            "keyword": "oscillating forest canopy",
            "dataFact": "波动",
            "contextDescription": "季度销售额存在明显周期性",
            "defaultPlan": [
                {"dataField": "季度", "subitemId": "canopy_line", "channels": ["position"]},
                {"dataField": "销售额", "subitemId": "canopy_band", "channels": ["lightness"]},
            ],
        },
        {
            "keyword": "steady river path",
            "dataFact": "平稳",
            "contextDescription": "服务器响应时间长期稳定",
            "defaultPlan": [
                {"dataField": "时间", "subitemId": "river_line", "channels": ["position"]},
                {"dataField": "响应时间", "subitemId": "river_points", "channels": ["size"]},
            ],
        },
    ]


def main():
    # 生成 Prompt1（新结构）
    items = sample_inputs()
    outputs = []

    for i, payload in enumerate(items, 1):
        result = build_prompt1(payload)
        outputs.append({
            "index": i,
            "payload": payload,
            "prompt1": result["prompt1"],
            "meta": result["meta"],
        })

    # 保存 prompts 到 outputs 目录
    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "agent7_v1_prompts_from_test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(outputs, f, ensure_ascii=False, indent=2)
    print(f"Saved prompts to {out_path}")

    # 不执行生成图片（单测仅保留 Prompt1 输出）


if __name__ == "__main__":
    main()


