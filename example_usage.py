#!/usr/bin/env python3
"""
简单使用示例
"""

from text_coordinate_finder import find_text_coordinates, find_text_coordinates_detailed

# 使用示例
def example():
    # 要搜索的文字
    search_text = "Hello World"
    
    # PDF文件路径
    pdf_file = "your_document.pdf"
    
    # 基础搜索 - 返回简单的坐标信息
    results = find_text_coordinates(search_text, pdf_file)
    
    if results:
        print(f"找到 {len(results)} 个 '{search_text}' 的匹配项:")
        for i, result in enumerate(results, 1):
            print(f"{i}. 页码: {result['page']}")
            print(f"   坐标: {result['bbox']}")  # [x0, y0, x1, y1]
            print(f"   左上角: ({result['bbox'][0]}, {result['bbox'][1]})")
            print(f"   右下角: ({result['bbox'][2]}, {result['bbox'][3]})")
            print()
    else:
        print(f"未找到 '{search_text}'")

# 详细信息示例
def detailed_example():
    search_text = "重要信息"
    pdf_file = "document.pdf"
    
    # 详细搜索 - 返回更多信息
    detailed_results = find_text_coordinates_detailed(search_text, pdf_file)
    
    for result in detailed_results:
        print(f"找到文字: {result['text']}")
        print(f"页码: {result['page']}")
        print(f"坐标: {result['bbox']}")
        print(f"距离左边: {result['position_info']['distance_from_left']:.1f}")
        print(f"距离顶部: {result['position_info']['distance_from_top']:.1f}")
        print(f"文字宽度: {result['position_info']['width']:.1f}")
        print(f"文字高度: {result['position_info']['height']:.1f}")
        print(f"上下文: {result['context']}")
        print("-" * 50)

if __name__ == "__main__":
    # 运行示例（需要替换为实际的PDF文件路径）
    print("请修改 pdf_file 变量为您的实际PDF文件路径")
    # example()
    # detailed_example() 