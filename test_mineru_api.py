#!/usr/bin/env python3
"""
测试MinerU文本定位接口
"""

import requests
import json


def test_mineru_locate_api():
    """测试MinerU文本定位接口"""
    
    # API端点
    base_url = "http://localhost:8004"
    endpoint = f"{base_url}/mineru-locate"
    
    # 测试数据
    test_data = {
        "filename": "航天电子产品常见质量缺陷案例.13610530(2)",
        "text": "航天科技图书出版基金资助出版",
        "similarity_threshold": 0.5,
        "page_number": 0
    }
    
    print(f"🔍 测试MinerU文本定位接口")
    print(f"📋 测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    print(f"🌐 发送请求到: {endpoint}")
    
    try:
        # 发送POST请求
        response = requests.post(endpoint, json=test_data, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            print(f"📄 响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 分析结果
            if result.get('success'):
                results = result.get('results', [])
                print(f"\n🎯 找到 {len(results)} 个匹配结果:")
                for i, match in enumerate(results):
                    print(f"  结果 {i+1}:")
                    print(f"    页面索引: {match['page_idx']}")
                    print(f"    相似度: {match['similarity']}")
                    print(f"    文本块数量: {match['block_count']}")
                    print(f"    边界框: {match['bbox']}")
                    print(f"    匹配文本预览: {match['matched_text_preview'][:100]}...")
            else:
                print(f"❌ 定位失败: {result.get('message')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败，请确保API服务正在运行 (http://localhost:8004)")
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")


def test_api_info():
    """测试API基础信息"""
    
    base_url = "http://localhost:8004"
    
    print(f"\n🏠 测试API基础信息")
    
    try:
        # 测试根端点
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API服务运行正常")
            print(f"📋 可用端点:")
            for endpoint, desc in result.get('endpoints', {}).items():
                print(f"  {endpoint}: {desc}")
        else:
            print(f"❌ API服务异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 无法连接API服务: {str(e)}")


def test_docs_info():
    """测试API文档信息"""
    
    base_url = "http://localhost:8004"
    endpoint = f"{base_url}/docs-info"
    
    print(f"\n📚 测试API文档信息")
    
    try:
        response = requests.get(endpoint, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取文档信息成功")
            print(f"📋 示例数据:")
            examples = result.get('examples', {})
            for name, example in examples.items():
                print(f"  {name}: {json.dumps(example, ensure_ascii=False)}")
        else:
            print(f"❌ 获取文档信息失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 获取文档信息错误: {str(e)}")


def test_page_number_feature():
    """测试page_number参数功能"""
    
    base_url = "http://localhost:8004"
    endpoint = f"{base_url}/mineru-locate"
    
    print(f"\n🔍 测试page_number参数功能")
    
    # 测试数据 - 从第13页开始搜索
    test_data = {
        "filename": "航天电子产品常见质量缺陷案例.13610530(2)",
        "text": "元器件安装孔与元器件引线不匹配",
        "similarity_threshold": 0.2,
        "page_number": 13
    }
    
    print(f"📋 测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求
        response = requests.post(endpoint, json=test_data, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            
            if result.get('success'):
                results = result.get('results', [])
                print(f"🎯 从第{test_data['page_number']}页开始找到 {len(results)} 个匹配结果:")
                for i, match in enumerate(results[:3]):  # 只显示前3个结果
                    print(f"  结果 {i+1}:")
                    print(f"    页面索引: {match['page_idx']} (应该 >= {test_data['page_number']})")
                    print(f"    相似度: {match['similarity']}")
                    print(f"    匹配文本: {match['matched_text_preview'][:50]}...")
                    
                # 验证结果是否符合page_number要求
                invalid_results = [r for r in results if r['page_idx'] < test_data['page_number']]
                if invalid_results:
                    print(f"❌ 发现 {len(invalid_results)} 个不符合page_number要求的结果!")
                else:
                    print(f"✅ 所有结果都符合page_number要求")
            else:
                print(f"❌ 定位失败: {result.get('message')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")


if __name__ == "__main__":
    print("🚀 开始测试MinerU文本定位API\n")
    
    # 测试基础信息
    test_api_info()
    
    # 测试文档信息
    test_docs_info()
    
    # 测试核心功能
    test_mineru_locate_api()
    
    # 测试page_number参数功能
    test_page_number_feature()
    
    print(f"\n🏁 测试完成")
    print(f"💡 要查看交互式API文档，请访问: http://localhost:8004/docs")