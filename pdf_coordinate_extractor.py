#!/usr/bin/env python3
"""
PDF坐标提取工具
支持pdfplumber和PyMuPDF两种方法提取PDF中每个元素的坐标信息
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def extract_with_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """使用pdfplumber提取PDF坐标信息"""
    try:
        import pdfplumber
    except ImportError:
        print("请安装pdfplumber: pip install pdfplumber")
        return {}
    
    print(f"使用pdfplumber处理: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        result = {
            "method": "pdfplumber",
            "total_pages": len(pdf.pages),
            "pages": []
        }
        
        for page_num, page in enumerate(pdf.pages):
            print(f"  处理第 {page_num + 1} 页...")
            
            page_data = {
                "page_number": page_num + 1,
                "page_size": {
                    "width": page.width,
                    "height": page.height
                },
                "characters": [],
                "text_lines": [],
                "images": [],
                "rectangles": [],
                "curves": []
            }
            
            # 提取字符坐标
            for char in page.chars:
                page_data["characters"].append({
                    "text": char.get("text", ""),
                    "bbox": [char["x0"], char["y0"], char["x1"], char["y1"]],
                    "font": char.get("fontname", ""),
                    "size": char.get("size", 0),
                    "color": char.get("non_stroking_color", None)
                })
            
            # 提取文本行
            for line in page.extract_text().split('\n'):
                if line.strip():
                    page_data["text_lines"].append({
                        "text": line.strip()
                    })
            
            # 提取图像
            for img in page.images:
                page_data["images"].append({
                    "bbox": [img["x0"], img["y0"], img["x1"], img["y1"]],
                    "width": img.get("width", 0),
                    "height": img.get("height", 0)
                })
            
            # 提取矩形
            for rect in page.rects:
                page_data["rectangles"].append({
                    "bbox": [rect["x0"], rect["y0"], rect["x1"], rect["y1"]],
                    "linewidth": rect.get("linewidth", 0)
                })
            
            # 提取曲线
            for curve in page.curves:
                page_data["curves"].append({
                    "points": curve.get("pts", []),
                    "linewidth": curve.get("linewidth", 0)
                })
            
            result["pages"].append(page_data)
            
            # 创建可视化图像
            try:
                im = page.to_image(resolution=150)
                # 绘制字符边界框
                if page.chars:
                    im.draw_rects(page.chars)
                # 保存可视化图像
                output_path = f"page_{page_num + 1}_pdfplumber_visualization.png"
                im.save(output_path)
                print(f"    可视化图像已保存: {output_path}")
            except Exception as e:
                print(f"    创建可视化图像失败: {e}")
    
    return result


def extract_with_pymupdf(pdf_path: str) -> Dict[str, Any]:
    """使用PyMuPDF提取PDF坐标信息"""
    try:
        import pymupdf as fitz  # 新版本的导入方式
    except ImportError:
        try:
            import fitz  # 旧版本的导入方式
        except ImportError:
            print("请安装PyMuPDF: pip install pymupdf")
            return {}
    
    print(f"使用PyMuPDF处理: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    result = {
        "method": "PyMuPDF",
        "total_pages": doc.page_count,
        "pages": []
    }
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        print(f"  处理第 {page_num + 1} 页...")
        
        page_data = {
            "page_number": page_num + 1,
            "page_size": {
                "width": page.rect.width,
                "height": page.rect.height
            },
            "text_blocks": [],
            "characters": [],
            "images": [],
            "drawings": []
        }
        
        # 方法1: 使用rawdict获取字符级别的详细信息
        text_dict = page.get_text("rawdict")
        
        for block in text_dict["blocks"]:
            if block.get("type") == 0:  # 文本块
                for line in block["lines"]:
                    for span in line["spans"]:
                        # 处理字符信息
                        if "chars" in span:
                            for char in span["chars"]:
                                page_data["characters"].append({
                                    "text": char["c"],
                                    "bbox": char["bbox"],
                                    "origin": char["origin"],
                                    "font": span.get("font", ""),
                                    "size": span.get("size", 0),
                                    "color": span.get("color", 0)
                                })
                        
                        # 处理span信息
                        page_data["text_blocks"].append({
                            "text": span["text"],
                            "bbox": span["bbox"],
                            "font": span.get("font", ""),
                            "size": span.get("size", 0),
                            "flags": span.get("flags", 0),
                            "color": span.get("color", 0)
                        })
            
            elif block.get("type") == 1:  # 图像块
                page_data["images"].append({
                    "bbox": block["bbox"],
                    "width": block.get("width", 0),
                    "height": block.get("height", 0)
                })
        
        # 获取绘图对象
        drawings = page.get_drawings()
        for drawing in drawings:
            page_data["drawings"].append({
                "type": drawing.get("type", ""),
                "bbox": drawing.get("rect", [0, 0, 0, 0]),
                "items": len(drawing.get("items", []))
            })
        
        result["pages"].append(page_data)
        
        # 创建可视化图像
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2倍分辨率
            output_path = f"page_{page_num + 1}_pymupdf_visualization.png"
            pix.save(output_path)
            print(f"    页面图像已保存: {output_path}")
        except Exception as e:
            print(f"    创建页面图像失败: {e}")
    
    doc.close()
    return result


def create_sample_pdf():
    """创建一个示例PDF文件用于测试"""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            print("无法创建示例PDF，请手动提供PDF文件")
            return None
    
    # 创建新的PDF文档
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4尺寸
    
    # 添加一些文本
    text_content = [
        ("Hello World!", 50, 100, 16),
        ("这是中文测试文本", 50, 150, 14),
        ("坐标提取演示", 50, 200, 12),
        ("Different fonts and sizes", 50, 250, 10),
    ]
    
    for text, x, y, size in text_content:
        page.insert_text((x, y), text, fontsize=size)
    
    # 添加一些图形
    page.draw_rect(fitz.Rect(300, 100, 400, 200), color=(1, 0, 0), width=2)
    page.draw_circle(fitz.Point(450, 150), 30, color=(0, 1, 0), width=2)
    
    # 保存文件
    sample_path = "sample_pdf_for_testing.pdf"
    doc.save(sample_path)
    doc.close()
    
    print(f"示例PDF已创建: {sample_path}")
    return sample_path


def save_results(data: Dict[str, Any], output_file: str):
    """保存结果到JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到: {output_file}")


def main():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # 如果没有提供PDF文件，创建示例文件
        pdf_path = create_sample_pdf()
        if not pdf_path:
            print("请提供PDF文件路径作为参数")
            print("用法: python pdf_coordinate_extractor.py <pdf_file_path>")
            return
    
    if not Path(pdf_path).exists():
        print(f"文件不存在: {pdf_path}")
        return
    
    print("=" * 60)
    print("PDF坐标提取工具")
    print("=" * 60)
    
    # 使用pdfplumber提取
    print("\n1. 使用pdfplumber提取坐标...")
    pdfplumber_result = extract_with_pdfplumber(pdf_path)
    if pdfplumber_result:
        save_results(pdfplumber_result, "coordinates_pdfplumber.json")
    
    print("\n" + "-" * 40)
    
    # 使用PyMuPDF提取
    print("\n2. 使用PyMuPDF提取坐标...")
    pymupdf_result = extract_with_pymupdf(pdf_path)
    if pymupdf_result:
        save_results(pymupdf_result, "coordinates_pymupdf.json")
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("提取结果统计:")
    print("=" * 60)
    
    if pdfplumber_result:
        total_chars = sum(len(page["characters"]) for page in pdfplumber_result["pages"])
        total_images = sum(len(page["images"]) for page in pdfplumber_result["pages"])
        print(f"pdfplumber: 字符数 {total_chars}, 图像数 {total_images}")
    
    if pymupdf_result:
        total_chars = sum(len(page["characters"]) for page in pymupdf_result["pages"])
        total_images = sum(len(page["images"]) for page in pymupdf_result["pages"])
        total_drawings = sum(len(page["drawings"]) for page in pymupdf_result["pages"])
        print(f"PyMuPDF: 字符数 {total_chars}, 图像数 {total_images}, 绘图对象数 {total_drawings}")
    
    print("\n提取完成！检查生成的JSON文件和可视化图像。")


if __name__ == "__main__":
    main() 