#!/usr/bin/env python3
"""
测试文本剪切函数的正确性
"""

import sys
sys.path.append('.')

from rag_chunk_locator import *

def test_cut_text_by_percent():
    """测试 cut_text_by_percent 函数"""
    print("🧪 测试 cut_text_by_percent 函数")
    print("=" * 50)
    
    test_cases = [
        # (输入文本, 百分比, 期望结果, 测试描述)
        ("Hello World", 0.5, "Hello", "50% 剪切"),
        ("Hello World", 0.3, "Hel", "30% 剪切"),
        ("Hello World", 0.8, "Hello Wo", "80% 剪切"),
        ("Hello World", 1.0, "Hello World", "100% 剪切"),
        ("Hello World", 0.0, "", "0% 剪切"),
        ("Hello World", 0.1, "H", "10% 剪切"),
        ("", 0.5, "", "空字符串测试"),
        ("A", 0.5, "A", "单字符测试"),
        ("测试中文", 0.5, "测试", "中文字符测试"),
        ("测试中文", 0.25, "测", "中文字符25%测试"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (text, percent, expected, description) in enumerate(test_cases, 1):
        result = cut_text_by_percent(text, percent)
        success = result == expected
        
        print(f"测试 {i}: {description}")
        print(f"  输入: '{text}', 百分比: {percent}")
        print(f"  期望: '{expected}'")
        print(f"  实际: '{result}'")
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        print()
        
        if success:
            passed += 1
    
    print(f"cut_text_by_percent 测试结果: {passed}/{total} 通过")
    return passed == total

def test_cut_text_by_percent_tail():
    """测试 cut_text_by_percent_tail 函数"""
    print("🧪 测试 cut_text_by_percent_tail 函数")
    print("=" * 50)
    
    test_cases = [
        # (输入文本, 百分比, 期望结果, 测试描述)
        ("Hello World", 0.5, "World", "50% 后缀剪切"),
        ("Hello World", 0.3, "rld", "30% 后缀剪切"),
        ("Hello World", 0.8, "o World", "80% 后缀剪切"),
        ("Hello World", 1.0, "Hello World", "100% 后缀剪切"),
        ("Hello World", 0.0, "", "0% 后缀剪切"),
        ("Hello World", 0.1, "d", "10% 后缀剪切"),
        ("", 0.5, "", "空字符串后缀测试"),
        ("A", 0.5, "A", "单字符后缀测试"),
        ("测试中文", 0.5, "中文", "中文字符后缀测试"),
        ("测试中文", 0.25, "文", "中文字符25%后缀测试"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (text, percent, expected, description) in enumerate(test_cases, 1):
        result = cut_text_by_percent_tail(text, percent)
        success = result == expected
        
        print(f"测试 {i}: {description}")
        print(f"  输入: '{text}', 百分比: {percent}")
        print(f"  期望: '{expected}'")
        print(f"  实际: '{result}'")
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        print()
        
        if success:
            passed += 1
    
    print(f"cut_text_by_percent_tail 测试结果: {passed}/{total} 通过")
    return passed == total

def test_edge_cases():
    """测试边界情况"""
    print("🧪 测试边界情况")
    print("=" * 50)
    
    edge_cases = [
        # (函数名, 输入文本, 百分比, 期望结果, 描述)
        ("前缀", "Test", 1.2, "Test", "百分比超过100%"),
        ("前缀", "Test", -0.1, "", "负数百分比"),
        ("前缀", "Test", 0.0, "", "零百分比"),
        ("后缀", "Test", 1.2, "Test", "百分比超过100%"),
        ("后缀", "Test", -0.1, "", "负数百分比"),
        ("后缀", "Test", 0.0, "", "零百分比"),
    ]
    
    passed = 0
    total = len(edge_cases)
    
    for i, (func_type, text, percent, expected, description) in enumerate(edge_cases, 1):
        if func_type == "前缀":
            result = cut_text_by_percent(text, percent)
        else:
            result = cut_text_by_percent_tail(text, percent)
        
        success = result == expected
        
        print(f"边界测试 {i}: {description}")
        print(f"  函数: {func_type}剪切")
        print(f"  输入: '{text}', 百分比: {percent}")
        print(f"  期望: '{expected}'")
        print(f"  实际: '{result}'")
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        print()
        
        if success:
            passed += 1
    
    print(f"边界情况测试结果: {passed}/{total} 通过")
    return passed == total

def test_visual_comparison():
    """可视化比较测试"""
    print("🧪 可视化比较测试")
    print("=" * 50)
    
    test_text = "这是一个测试文本，用于验证剪切函数"
    print(f"测试文本: '{test_text}'")
    print(f"文本长度: {len(test_text)} 字符")
    print()
    
    percentages = [0.1, 0.25, 0.5, 0.75, 0.9]
    
    print("前缀剪切结果:")
    for percent in percentages:
        result = cut_text_by_percent(test_text, percent)
        print(f"  {percent*100:>3.0f}%: '{result}' ({len(result)} 字符)")
    
    print("\n后缀剪切结果:")
    for percent in percentages:
        result = cut_text_by_percent_tail(test_text, percent)
        print(f"  {percent*100:>3.0f}%: '{result}' ({len(result)} 字符)")
    
    print("\n✅ 可视化比较完成")

def main():
    """运行所有测试"""
    print("🚀 开始测试文本剪切函数")
    print("=" * 60)
    
    # 运行所有测试
    test1_passed = test_cut_text_by_percent()
    print("\n" + "=" * 60 + "\n")
    
    test2_passed = test_cut_text_by_percent_tail()
    print("\n" + "=" * 60 + "\n")
    
    test3_passed = test_edge_cases()
    print("\n" + "=" * 60 + "\n")
    
    test_visual_comparison()
    print("\n" + "=" * 60)
    
    # 总结
    all_passed = test1_passed and test2_passed and test3_passed
    
    print("\n📊 测试总结:")
    print(f"  cut_text_by_percent: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"  cut_text_by_percent_tail: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"  边界情况: {'✅ 通过' if test3_passed else '❌ 失败'}")
    print(f"  总体结果: {'🎉 所有测试通过' if all_passed else '⚠️ 部分测试失败'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 