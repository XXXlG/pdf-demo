#!/usr/bin/env python3
"""
RAG匹配结果验证工具
用于验证和可视化RAG切片在PDF中的匹配结果
"""

import re
from typing import Dict, Any, List
from difflib import SequenceMatcher

def verify_match_result(original_chunk: str, pdf_path: str, match_result: Dict[str, Any], 
                       create_visual: bool = True) -> Dict[str, Any]:
    """
    验证匹配结果的准确性
    
    Args:
        original_chunk: 原始切片文本
        pdf_path: PDF文件路径
        match_result: 匹配结果字典
        create_visual: 是否创建可视化验证
    
    Returns:
        验证报告
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install pymupdf")
    
    print("🔍 开始验证匹配结果...")
    print("=" * 50)
    
    # 1. 基本信息验证
    page_num = match_result["page"] - 1  # 转换为0索引
    bbox = match_result["bbox"]
    
    print(f"📄 目标页码: {match_result['page']}")
    print(f"📍 匹配坐标: {bbox}")
    print(f"📊 报告相似度: {match_result['similarity']:.3f}")
    
    # 2. 提取实际匹配区域的完整文本
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install pymupdf")
    
    doc = fitz.open(pdf_path)
    
    if page_num >= doc.page_count:
        return {"error": f"页码超出范围，PDF只有{doc.page_count}页"}
    
    page = doc[page_num]
    
    # 提取匹配区域的文本
    match_rect = fitz.Rect(bbox)
    extracted_text = page.get_textbox(match_rect)
    extracted_text_clean = _clean_text_for_comparison(extracted_text)
    
    print(f"\n📝 提取的完整匹配文本:")
    print(f"原始长度: {len(extracted_text)} 字符")
    print(f"清理后长度: {len(extracted_text_clean)} 字符")
    print("-" * 30)
    print(extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text)
    print("-" * 30)
    
    # 3. 重新计算相似度
    original_clean = _clean_text_for_comparison(original_chunk)
    actual_similarity = _calculate_detailed_similarity(original_clean, extracted_text_clean)
    
    print(f"\n📊 详细相似度分析:")
    print(f"报告相似度: {match_result['similarity']:.3f}")
    print(f"实际相似度: {actual_similarity['overall']:.3f}")
    print(f"字符级匹配: {actual_similarity['char_level']:.3f}")
    print(f"词汇级匹配: {actual_similarity['word_level']:.3f}")
    print(f"关键词覆盖: {actual_similarity['keyword_coverage']:.3f}")
    
    # 4. 文本对比分析
    comparison = _analyze_text_differences(original_clean, extracted_text_clean)
    print(f"\n🔍 文本对比分析:")
    print(f"共同词汇: {len(comparison['common_words'])}")
    print(f"缺失词汇: {len(comparison['missing_words'])}")
    print(f"多余词汇: {len(comparison['extra_words'])}")
    
    if comparison['missing_words']:
        print(f"主要缺失词汇: {comparison['missing_words'][:5]}")
    
    # 5. 创建可视化验证
    verification_report = {
        "page": match_result["page"],
        "bbox": bbox,
        "reported_similarity": match_result["similarity"],
        "actual_similarity": actual_similarity,
        "text_comparison": comparison,
        "extracted_text": extracted_text[:500],  # 前500字符
        "verification_status": "PASS" if actual_similarity["overall"] > 0.3 else "FAIL"
    }
    
    if create_visual:
        visual_path = _create_visual_verification(doc, page_num, match_rect, pdf_path)
        verification_report["visual_verification"] = visual_path
        print(f"\n🖼️  可视化验证已保存: {visual_path}")
    
    doc.close()
    
    # 6. 生成验证结论
    print(f"\n✅ 验证结论:")
    if verification_report["verification_status"] == "PASS":
        print(f"   ✓ 匹配结果有效 (相似度: {actual_similarity['overall']:.3f})")
        print(f"   ✓ 找到了相关内容区域")
    else:
        print(f"   ❌ 匹配结果可疑 (相似度: {actual_similarity['overall']:.3f})")
        print(f"   ❌ 可能需要调整匹配参数")
    
    return verification_report


def _clean_text_for_comparison(text: str) -> str:
    """为对比分析清理文本"""
    if not text:
        return ""
    
    # 移除多余空格和特殊字符
    text = re.sub(r'\s+', ' ', text.strip())
    # 移除图片引用等
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    # 标准化标点
    text = re.sub(r'[，。！？；：、]', ' ', text)
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def _calculate_detailed_similarity(text1: str, text2: str) -> Dict[str, float]:
    """计算详细的相似度指标"""
    if not text1 or not text2:
        return {"overall": 0.0, "char_level": 0.0, "word_level": 0.0, "keyword_coverage": 0.0}
    
    # 字符级相似度
    char_similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    # 词汇级相似度
    words1 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{2,}', text1.lower()))
    words2 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{2,}', text2.lower()))
    
    if words1 and words2:
        word_similarity = len(words1 & words2) / len(words1 | words2)
    else:
        word_similarity = 0.0
    
    # 关键词覆盖率
    keywords1 = [w for w in words1 if len(w) >= 3]
    keywords2 = [w for w in words2 if len(w) >= 3]
    
    if keywords1:
        keyword_coverage = len(set(keywords1) & set(keywords2)) / len(keywords1)
    else:
        keyword_coverage = 0.0
    
    # 综合相似度
    overall = (char_similarity * 0.3 + word_similarity * 0.4 + keyword_coverage * 0.3)
    
    return {
        "overall": overall,
        "char_level": char_similarity,
        "word_level": word_similarity,
        "keyword_coverage": keyword_coverage
    }


def _analyze_text_differences(text1: str, text2: str) -> Dict[str, List[str]]:
    """分析两段文本的差异"""
    words1 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{2,}', text1.lower()))
    words2 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{2,}', text2.lower()))
    
    return {
        "common_words": list(words1 & words2),
        "missing_words": list(words1 - words2),
        "extra_words": list(words2 - words1)
    }


def _create_visual_verification(doc, page_num: int, match_rect, pdf_path: str) -> str:
    """创建可视化验证图片"""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            print("无法导入PyMuPDF，跳过可视化验证")
            return None
    
    try:
        page = doc[page_num]
        
        # 在匹配区域绘制红色边框
        page.draw_rect(match_rect, color=(1, 0, 0), width=2)
        
        # 添加标注
        text_point = fitz.Point(match_rect.x0, match_rect.y0 - 10)
        page.insert_text(text_point, f"匹配区域 {match_rect.width:.0f}x{match_rect.height:.0f}", 
                        fontsize=10, color=(1, 0, 0))
        
        # 保存为图片
        output_path = pdf_path.replace('.pdf', f'_verification_page_{page_num + 1}.png')
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放提高清晰度
        pix.save(output_path)
        
        return output_path
        
    except Exception as e:
        print(f"创建可视化验证失败: {e}")
        return None


def quick_verify():
    """快速验证最近的匹配结果"""
    
    # 使用示例数据
    from rag_chunk_locator import find_rag_chunk_coordinates
    
    knowledge_chunk = r"""
1）元器件安装孔与元器件引线不匹配# 问题描述印制板元器件安装孔孔径与元器件引线直径不匹配，导致元器件引线无法安装或间隙过小，容易导致安装孔损伤或透锡不良，影响焊点的可靠性，见图1-1所示。
    """
    
    pdf_file = "data/航天电子产品常见质量缺陷案例.13610530(2).pdf"
    
    print("🚀 执行快速验证...")
    
    try:
        # 获取匹配结果
        results = find_rag_chunk_coordinates(knowledge_chunk, pdf_file, return_best_only=True)
        
        if results:
            result = results[0]
            
            # 验证结果
            verification = verify_match_result(knowledge_chunk, pdf_file, result, create_visual=True)
            
            print(f"\n📋 验证摘要:")
            print(f"   状态: {verification['verification_status']}")
            print(f"   实际相似度: {verification['actual_similarity']['overall']:.3f}")
            print(f"   关键词覆盖: {verification['actual_similarity']['keyword_coverage']:.3f}")
            
            return verification
        else:
            print("❌ 没有找到匹配结果")
            return None
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return None


if __name__ == "__main__":
    # 运行快速验证
    quick_verify() 