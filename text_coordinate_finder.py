#!/usr/bin/env python3
"""
PDF文字坐标查找器
输入文字和PDF路径，返回文字在PDF中的坐标信息
"""

def find_text_coordinates(text: str, pdf_path: str):
    """
    在PDF中查找指定文字的坐标
    
    Args:
        text (str): 要搜索的文字
        pdf_path (str): PDF文件路径
    
    Returns:
        list: 包含坐标信息的列表，每个元素格式为：
              {
                  "page": 页码,
                  "text": 找到的文字,
                  "bbox": [x0, y0, x1, y1],  # 边界框坐标
                  "rect": [x0, y0, x1, y1]   # 矩形坐标 (同bbox)
              }
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install pymupdf")
    
    results = []
    
    # 打开PDF文档
    doc = fitz.open(pdf_path)
    
    # 遍历每一页搜索文字
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # 搜索文字
        text_instances = page.search_for(text)
        
        # 处理搜索结果
        for rect in text_instances:
            results.append({
                "page": page_num + 1,  # 页码从1开始
                "text": text,
                "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                "rect": [rect.x0, rect.y0, rect.x1, rect.y1]
            })
    
    doc.close()
    return results


def find_text_coordinates_detailed(text: str, pdf_path: str):
    """
    在PDF中查找指定文字的详细坐标信息（包含更多上下文）
    
    Args:
        text (str): 要搜索的文字
        pdf_path (str): PDF文件路径
    
    Returns:
        list: 包含详细坐标信息的列表
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install pymupdf")
    
    results = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # 搜索文字
        text_instances = page.search_for(text)
        
        if text_instances:
            # 获取页面的文字信息用于上下文
            page_text = page.get_text("dict")
            
            for rect in text_instances:
                # 获取周围的文字作为上下文
                expanded_rect = fitz.Rect(
                    max(0, rect.x0 - 50),
                    max(0, rect.y0 - 20), 
                    min(page.rect.width, rect.x1 + 50),
                    min(page.rect.height, rect.y1 + 20)
                )
                
                context_text = page.get_textbox(expanded_rect)
                
                results.append({
                    "page": page_num + 1,
                    "page_size": {
                        "width": page.rect.width,
                        "height": page.rect.height
                    },
                    "text": text,
                    "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                    "context": context_text.strip(),
                    "position_info": {
                        "distance_from_left": rect.x0,
                        "distance_from_top": rect.y0,
                        "distance_from_right": page.rect.width - rect.x1,
                        "distance_from_bottom": page.rect.height - rect.y1,
                        "width": rect.width,
                        "height": rect.height
                    }
                })
    
    doc.close()
    return results


# 使用示例和测试函数
def demo():
    """演示如何使用这些函数"""
    
    # 创建测试PDF
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            print("需要安装PyMuPDF来运行演示")
            return
    
    # 创建示例PDF
    doc = fitz.open()
    page = doc.new_page()
    
    # 添加测试文字
    test_texts = [
        ("Hello World", 100, 100),
        ("PDF坐标测试", 100, 150),
        ("这是一个示例文档", 100, 200),
        ("Find me!", 300, 300),
        ("重复文字", 100, 250),
        ("重复文字", 400, 250),
    ]
    
    for text, x, y in test_texts:
        page.insert_text((x, y), text, fontsize=12)
    
    test_pdf = "test_coordinates.pdf"
    doc.save(test_pdf)
    doc.close()
    print(f"测试PDF已创建: {test_pdf}")
    
    # 测试搜索功能
    search_terms = ["Hello World", "PDF坐标测试", "重复文字", "Find me!"]
    
    for term in search_terms:
        print(f"\n搜索文字: '{term}'")
        
        # 基础搜索
        results = find_text_coordinates(term, test_pdf)
        print(f"找到 {len(results)} 个匹配项:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. 页码: {result['page']}, 坐标: {result['bbox']}")
        
        # 详细搜索（只显示第一个结果的详细信息）
        if results:
            detailed = find_text_coordinates_detailed(term, test_pdf)
            if detailed:
                detail = detailed[0]
                print(f"  详细信息:")
                print(f"    距离左边: {detail['position_info']['distance_from_left']:.1f}")
                print(f"    距离顶部: {detail['position_info']['distance_from_top']:.1f}")
                print(f"    文字大小: {detail['position_info']['width']:.1f} x {detail['position_info']['height']:.1f}")
                print(f"    上下文: {detail['context'][:50]}...")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        # 命令行使用方式
        text_to_find = sys.argv[1]
        pdf_file = sys.argv[2]
        
        print(f"在PDF '{pdf_file}' 中搜索文字: '{text_to_find}'")
        
        results = find_text_coordinates(text_to_find, pdf_file)
        
        if results:
            print(f"找到 {len(results)} 个匹配项:")
            for i, result in enumerate(results, 1):
                print(f"{i}. 页码: {result['page']}, 坐标: {result['bbox']}")
        else:
            print("未找到匹配的文字")
            
    else:
        # 运行演示
        print("PDF文字坐标查找器演示")
        print("=" * 40)
        demo()
        print("\n" + "=" * 40)
        print("用法:")
        print("python text_coordinate_finder.py '要搜索的文字' 'path/to/file.pdf'") 