#!/usr/bin/env python3
"""
增强版PDF文字坐标查找器
支持多行文本、图片OCR、表格等复杂情况
"""

import re
from typing import List, Dict, Any, Optional

def find_text_coordinates_advanced(text: str, pdf_path: str, 
                                   ignore_case: bool = False,
                                   multiline: bool = True,
                                   with_ocr: bool = False) -> List[Dict[str, Any]]:
    """
    在PDF中查找指定文字的坐标（增强版）
    
    Args:
        text (str): 要搜索的文字，支持正则表达式
        pdf_path (str): PDF文件路径
        ignore_case (bool): 是否忽略大小写
        multiline (bool): 是否支持跨行搜索
        with_ocr (bool): 是否对图片进行OCR识别
    
    Returns:
        list: 包含坐标信息的列表
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
        
        # 1. 常规文本搜索
        page_results = _search_regular_text(page, text, page_num, ignore_case, multiline)
        results.extend(page_results)
        
        # 2. 表格文本搜索
        table_results = _search_table_text(page, text, page_num, ignore_case)
        results.extend(table_results)
        
        # 3. OCR图片文本搜索（如果启用）
        if with_ocr:
            ocr_results = _search_ocr_text(page, text, page_num, ignore_case)
            results.extend(ocr_results)
    
    doc.close()
    return results


def _search_regular_text(page, text: str, page_num: int, ignore_case: bool, multiline: bool) -> List[Dict[str, Any]]:
    """搜索常规文本"""
    results = []
    
    # 基础搜索
    flags = 0
    if ignore_case:
        try:
            import pymupdf as fitz
            flags = fitz.TEXT_INHIBIT_SPACES  # 忽略空格差异
        except:
            pass
    
    # 直接搜索
    text_instances = page.search_for(text, flags=flags)
    for rect in text_instances:
        results.append({
            "page": page_num + 1,
            "text": text,
            "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
            "type": "direct_match",
            "confidence": 1.0
        })
    
    # 如果启用多行搜索且没有直接找到
    if multiline and not text_instances:
        multiline_results = _search_multiline_text(page, text, page_num, ignore_case)
        results.extend(multiline_results)
    
    return results


def _search_multiline_text(page, text: str, page_num: int, ignore_case: bool) -> List[Dict[str, Any]]:
    """搜索跨行文本"""
    results = []
    
    # 获取页面的所有文本块
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            return results
    
    # 获取文本块
    text_dict = page.get_text("dict")
    
    # 提取所有文本和位置信息
    text_segments = []
    
    for block in text_dict["blocks"]:
        if block.get("type") == 0:  # 文本块
            for line in block["lines"]:
                line_text = ""
                line_bbox = line["bbox"]
                
                for span in line["spans"]:
                    line_text += span["text"]
                
                if line_text.strip():
                    text_segments.append({
                        "text": line_text.strip(),
                        "bbox": line_bbox
                    })
    
    # 合并连续的文本段落进行搜索
    search_text = text.lower() if ignore_case else text
    
    for i in range(len(text_segments)):
        # 从当前位置开始，尝试组合多行文本
        combined_text = ""
        combined_bbox = None
        
        for j in range(i, min(i + 10, len(text_segments))):  # 最多检查10行
            if combined_text:
                combined_text += " " + text_segments[j]["text"]
            else:
                combined_text = text_segments[j]["text"]
            
            # 更新边界框
            current_bbox = text_segments[j]["bbox"]
            if combined_bbox is None:
                combined_bbox = list(current_bbox)
            else:
                combined_bbox[0] = min(combined_bbox[0], current_bbox[0])  # x0
                combined_bbox[1] = min(combined_bbox[1], current_bbox[1])  # y0
                combined_bbox[2] = max(combined_bbox[2], current_bbox[2])  # x1
                combined_bbox[3] = max(combined_bbox[3], current_bbox[3])  # y1
            
            # 检查是否包含目标文本
            check_text = combined_text.lower() if ignore_case else combined_text
            if search_text in check_text:
                # 计算匹配度
                confidence = len(search_text) / len(combined_text) if combined_text else 0
                
                results.append({
                    "page": page_num + 1,
                    "text": text,
                    "bbox": combined_bbox,
                    "found_text": combined_text,
                    "type": "multiline_match",
                    "confidence": min(confidence, 1.0),
                    "lines_spanned": j - i + 1
                })
                break
    
    return results


def _search_table_text(page, text: str, page_num: int, ignore_case: bool) -> List[Dict[str, Any]]:
    """搜索表格中的文本"""
    results = []
    
    try:
        import pymupdf as fitz
    except ImportError:
        return results
    
    # 检测表格（通过线条和矩形）
    drawings = page.get_drawings()
    tables = _detect_tables(page, drawings)
    
    if not tables:
        return results
    
    # 在每个表格区域搜索文本
    for table_area in tables:
        table_rect = fitz.Rect(table_area)
        
        # 获取表格区域内的文本
        table_text = page.get_textbox(table_rect)
        
        search_text = text.lower() if ignore_case else text
        check_text = table_text.lower() if ignore_case else table_text
        
        if search_text in check_text:
            # 尝试更精确地定位文本在表格中的位置
            table_instances = page.search_for(text, clip=table_rect)
            
            if table_instances:
                for rect in table_instances:
                    results.append({
                        "page": page_num + 1,
                        "text": text,
                        "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "type": "table_match",
                        "table_area": table_area,
                        "confidence": 0.9
                    })
            else:
                # 如果精确搜索失败，返回整个表格区域
                results.append({
                    "page": page_num + 1,
                    "text": text,
                    "bbox": table_area,
                    "found_text": table_text,
                    "type": "table_area_match",
                    "confidence": 0.7
                })
    
    return results


def _detect_tables(page, drawings) -> List[List[float]]:
    """检测页面中的表格区域"""
    try:
        import pymupdf as fitz
    except ImportError:
        return []
    
    # 简单的表格检测：寻找矩形密集的区域
    rects = []
    
    for drawing in drawings:
        if drawing.get("type") == "re":  # 矩形
            rect = drawing.get("rect", [])
            if len(rect) == 4:
                rects.append(rect)
    
    # 合并相近的矩形来形成表格区域
    if len(rects) > 3:  # 至少需要几个矩形才可能是表格
        # 这里可以实现更复杂的表格检测算法
        # 简化版本：返回包含最多矩形的区域
        if rects:
            min_x = min(rect[0] for rect in rects)
            min_y = min(rect[1] for rect in rects)
            max_x = max(rect[2] for rect in rects)
            max_y = max(rect[3] for rect in rects)
            
            return [[min_x, min_y, max_x, max_y]]
    
    return []


def _search_ocr_text(page, text: str, page_num: int, ignore_case: bool) -> List[Dict[str, Any]]:
    """对图片进行OCR并搜索文本"""
    results = []
    
    try:
        import pymupdf as fitz
    except ImportError:
        return results
    
    # 获取页面中的图像
    image_list = page.get_images()
    
    for img_index, img in enumerate(image_list):
        try:
            # 获取图像
            xref = img[0]
            pix = fitz.Pixmap(page.parent, xref)
            
            if pix.n - pix.alpha < 4:  # 确保不是CMYK
                # 进行OCR（需要安装pytesseract）
                ocr_text = _perform_ocr(pix)
                
                if ocr_text:
                    search_text = text.lower() if ignore_case else text
                    check_text = ocr_text.lower() if ignore_case else ocr_text
                    
                    if search_text in check_text:
                        # 获取图像在页面中的位置
                        img_rect = page.get_image_rects(xref)
                        
                        if img_rect:
                            for rect in img_rect:
                                results.append({
                                    "page": page_num + 1,
                                    "text": text,
                                    "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                                    "found_text": ocr_text,
                                    "type": "ocr_match",
                                    "confidence": 0.8,
                                    "image_index": img_index
                                })
            
            pix = None  # 释放内存
            
        except Exception as e:
            print(f"OCR处理图像 {img_index} 时出错: {e}")
            continue
    
    return results


def _perform_ocr(pix) -> str:
    """对图像执行OCR"""
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # 将PyMuPDF的Pixmap转换为PIL Image
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        # 执行OCR
        ocr_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return ocr_text.strip()
        
    except ImportError:
        print("OCR功能需要安装: pip install pytesseract pillow")
        return ""
    except Exception as e:
        print(f"OCR处理失败: {e}")
        return ""


def find_text_with_regex(pattern: str, pdf_path: str) -> List[Dict[str, Any]]:
    """使用正则表达式搜索文本"""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install pymupdf")
    
    results = []
    doc = fitz.open(pdf_path)
    
    regex = re.compile(pattern)
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # 获取页面文本
        page_text = page.get_text()
        
        # 查找所有匹配
        matches = regex.finditer(page_text)
        
        for match in matches:
            matched_text = match.group()
            
            # 搜索匹配文本的位置
            text_instances = page.search_for(matched_text)
            
            for rect in text_instances:
                results.append({
                    "page": page_num + 1,
                    "text": matched_text,
                    "pattern": pattern,
                    "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                    "type": "regex_match",
                    "match_groups": match.groups()
                })
    
    doc.close()
    return results


# 演示函数
def demo_advanced():
    """演示增强功能"""
    try:
        import pymupdf as fitz
    except ImportError:
        print("需要安装PyMuPDF来运行演示")
        return
    
    # 创建复杂的测试PDF
    doc = fitz.open()
    page = doc.new_page()
    
    # 添加多行文本
    page.insert_text((50, 100), "这是第一行文本", fontsize=12)
    page.insert_text((50, 120), "这是第二行，包含关键", fontsize=12)
    page.insert_text((50, 140), "信息在这里", fontsize=12)
    
    # 添加表格（简单模拟）
    table_rect = fitz.Rect(200, 200, 500, 350)
    page.draw_rect(table_rect, width=1)
    
    # 表格内容
    page.insert_text((220, 230), "姓名", fontsize=10)
    page.insert_text((320, 230), "年龄", fontsize=10)
    page.insert_text((420, 230), "城市", fontsize=10)
    
    page.insert_text((220, 250), "张三", fontsize=10)
    page.insert_text((320, 250), "25", fontsize=10)
    page.insert_text((420, 250), "北京", fontsize=10)
    
    page.insert_text((220, 270), "李四", fontsize=10)
    page.insert_text((320, 270), "30", fontsize=10)
    page.insert_text((420, 270), "上海", fontsize=10)
    
    # 添加分隔线
    for y in [210, 240, 260]:
        page.draw_line(fitz.Point(200, y), fitz.Point(500, y), width=0.5)
    
    for x in [280, 380]:
        page.draw_line(fitz.Point(x, 200), fitz.Point(x, 350), width=0.5)
    
    test_pdf = "complex_test.pdf"
    doc.save(test_pdf)
    doc.close()
    print(f"复杂测试PDF已创建: {test_pdf}")
    
    # 测试各种搜索
    test_cases = [
        ("关键信息", "多行文本搜索"),
        ("张三", "表格文本搜索"),
        ("年龄", "表格标题搜索"),
        (r"\d+", "正则表达式搜索（数字）"),
    ]
    
    for search_term, description in test_cases:
        print(f"\n{description}: '{search_term}'")
        
        if search_term.startswith(r"\d"):
            # 正则表达式搜索
            results = find_text_with_regex(search_term, test_pdf)
        else:
            # 高级搜索
            results = find_text_coordinates_advanced(
                search_term, test_pdf, 
                multiline=True, 
                ignore_case=True
            )
        
        print(f"找到 {len(results)} 个匹配项:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. 页码: {result['page']}, 坐标: {result['bbox']}")
            print(f"      类型: {result['type']}")
            if 'confidence' in result:
                print(f"      置信度: {result['confidence']:.2f}")
            if 'found_text' in result:
                print(f"      找到的文本: {result['found_text'][:50]}...")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        text_to_find = sys.argv[1]
        pdf_file = sys.argv[2]
        
        # 检查额外参数
        use_ocr = "--ocr" in sys.argv
        ignore_case = "--ignore-case" in sys.argv
        multiline = "--multiline" in sys.argv or True  # 默认启用
        
        print(f"在PDF '{pdf_file}' 中搜索文字: '{text_to_find}'")
        print(f"多行搜索: {multiline}, OCR: {use_ocr}, 忽略大小写: {ignore_case}")
        
        results = find_text_coordinates_advanced(
            text_to_find, pdf_file,
            ignore_case=ignore_case,
            multiline=multiline,
            with_ocr=use_ocr
        )
        
        if results:
            print(f"找到 {len(results)} 个匹配项:")
            for i, result in enumerate(results, 1):
                print(f"{i}. 页码: {result['page']}, 坐标: {result['bbox']}")
                print(f"   类型: {result['type']}")
                if 'confidence' in result:
                    print(f"   置信度: {result['confidence']:.2f}")
                if 'found_text' in result and result['found_text'] != result['text']:
                    print(f"   实际找到: {result['found_text'][:100]}...")
                print()
        else:
            print("未找到匹配的文字")
    else:
        print("增强版PDF文字坐标查找器演示")
        print("=" * 50)
        demo_advanced()
        print("\n" + "=" * 50)
        print("用法:")
        print("python advanced_text_finder.py '要搜索的文字' 'file.pdf' [选项]")
        print("选项:")
        print("  --ocr           启用OCR识别图片中的文字")
        print("  --ignore-case   忽略大小写")
        print("  --multiline     启用多行搜索（默认启用）") 