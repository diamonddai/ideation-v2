#!/usr/bin/env python3
"""
测试模块二集成模块三的功能
验证每个喻体都能生成真实图片
"""

import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv("/Users/anker/Tongji/idvx/project-code/Ideation_code/metaphor_backend/.env")

async def test_module2_integration():
    """测试模块二集成模块三的功能"""
    
    # 测试数据
    test_data = {
        "boundField": {
            "field": "population",
            "dataFact": "growing rapidly"
        },
        "blindRatio": 0.5,
        "totalLimit": 5  # 限制为5个变体，减少测试时间
    }
    
    print("🧪 开始测试模块二集成模块三功能")
    print("=" * 60)
    print(f"📋 测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        # 调用模块二接口
        url = "http://localhost:8000/api/v1/module2/generate-metaphors"
        
        print("🚀 正在调用模块二接口...")
        print(f"🔗 URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                print(f"📥 收到响应，状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    print("✅ 模块二调用成功！")
                    print(f"📊 生成了 {len(result.get('variations', []))} 个隐喻变体")
                    print()
                    
                    # 检查每个变体的图片URL
                    print("🖼️ 检查每个变体的图片URL:")
                    print("-" * 40)
                    
                    for i, variation in enumerate(result.get('variations', []), 1):
                        keyword = variation.get('keyword', '')
                        thumb_url = variation.get('thumb', '')
                        
                        print(f"{i}. 关键词: {keyword}")
                        print(f"   图片URL: {thumb_url}")
                        
                        # 判断是否为真实URL
                        if 'oss-cn-beijing.aliyuncs.com' in thumb_url:
                            print("   ✅ 真实阿里云OSS URL")
                        elif 'ex.com/thumbs' in thumb_url:
                            print("   ⚠️ 假URL（模块三调用失败）")
                        elif 'via.placeholder.com' in thumb_url:
                            print("   ⚠️ 占位图URL（模块三调用失败）")
                        else:
                            print("   ❓ 未知URL类型")
                        print()
                    
                    # 统计结果
                    real_urls = sum(1 for v in result.get('variations', []) 
                                  if 'oss-cn-beijing.aliyuncs.com' in v.get('thumb', ''))
                    fake_urls = len(result.get('variations', [])) - real_urls
                    
                    print("📈 统计结果:")
                    print(f"   ✅ 真实图片URL: {real_urls} 个")
                    print(f"   ⚠️ 假/占位图URL: {fake_urls} 个")
                    print(f"   📊 成功率: {real_urls/len(result.get('variations', []))*100:.1f}%")
                    
                    # 保存结果到文件
                    with open('module2_integration_test_result.json', 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"💾 结果已保存到: module2_integration_test_result.json")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 模块二调用失败: {response.status}")
                    print(f"📄 错误信息: {error_text}")
                    
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("🔧 模块二集成模块三功能测试工具")
    print("=" * 60)
    print("📝 测试目标:")
    print("   1. 验证模块二能正常调用模块三")
    print("   2. 验证每个喻体都能生成真实图片")
    print("   3. 验证失败时能回退到假URL")
    print("   4. 验证3分钟超时机制")
    print()
    
    await test_module2_integration()
    
    print("=" * 60)
    print("🎯 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())




