#!/usr/bin/env python3
"""
RAG知识切片坐标定位器 - 优化版
专门用于在PDF中定位RAG系统的知识切片位置，返回最佳匹配区域
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
import json

def find_rag_chunk_coordinates(chunk_text: str, pdf_path: str, 
                              similarity_threshold: float = 0.7,
                              return_best_only: bool = True) -> List[Dict[str, Any]]:
    """
    在PDF中定位RAG知识切片的坐标 - 返回最佳匹配区域
    
    Args:
        chunk_text (str): RAG知识切片的文本内容
        pdf_path (str): PDF文件路径
        similarity_threshold (float): 文本相似度阈值 (0-1)
        return_best_only (bool): 是否只返回最佳匹配
    
    Returns:
        list: 包含切片位置信息的列表（默认只返回最佳匹配）
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install pymupdf")
    
    # 预处理切片文本
    chunk_text_clean = _clean_text(chunk_text)
    chunk_length = len(chunk_text_clean)
    
    print(f"正在分析切片... 长度: {chunk_length} 字符")
    
    # 根据文本长度选择不同的匹配策略
    if chunk_length < 100:
        print("📝 使用短文本匹配策略")
        return _find_short_text_coordinates(chunk_text_clean, pdf_path, similarity_threshold, return_best_only)
    else:
        print("📖 使用长文本匹配策略")
        return _find_long_text_coordinates(chunk_text_clean, pdf_path, similarity_threshold, return_best_only)


def _find_short_text_coordinates(chunk_text: str, pdf_path: str, 
                                similarity_threshold: float, return_best_only: bool) -> List[Dict[str, Any]]:
    """短文本匹配策略 - 更灵活的匹配方法"""
    
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    
    # 短文本使用更简单的关键词
    chunk_keywords = _extract_short_text_keywords(chunk_text)
    print(f"短文本关键词: {chunk_keywords[:3]}")
    
    results = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # 方法1: 直接文本搜索
        direct_matches = _find_direct_text_matches(page, chunk_text, page_num)
        results.extend(direct_matches)
        
        # 方法2: 关键词匹配（降低阈值）
        keyword_matches = _find_keyword_matches(page, chunk_keywords, chunk_text, page_num, similarity_threshold * 0.6)
        results.extend(keyword_matches)
        
        # 方法3: 模糊匹配（进一步降低阈值）
        fuzzy_matches = _find_fuzzy_matches(page, chunk_text, page_num, similarity_threshold * 0.4)
        results.extend(fuzzy_matches)
    
    doc.close()
    
    # 短文本结果处理
    results = _process_short_text_results(results, return_best_only)
    
    print(f"短文本匹配找到 {len(results)} 个结果")
    return results


def _find_long_text_coordinates(chunk_text: str, pdf_path: str, 
                               similarity_threshold: float, return_best_only: bool) -> List[Dict[str, Any]]:
    """长文本匹配策略 - 原有的整体匹配方法"""
    
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    
    chunk_keywords = _extract_key_phrases(chunk_text)
    print(f"长文本关键词: {chunk_keywords[:5]}")
    
    results = []
    doc = fitz.open(pdf_path)
    
    # 遍历每一页，寻找最佳匹配区域
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # 方法1: 整页文本匹配
        page_text = page.get_text()
        page_text_clean = _clean_text(page_text)
        
        # 计算整体相似度
        overall_similarity = _calculate_similarity(chunk_text, page_text_clean)
        
        if overall_similarity >= similarity_threshold:
            # 找到高相似度页面，定位具体区域
            best_region = _locate_best_region_in_page(
                page, chunk_text, chunk_keywords, page_num
            )
            if best_region:
                results.append(best_region)
        
        # 方法2: 关键词密度匹配
        elif _calculate_keyword_density(chunk_keywords, page_text_clean) > 0.3:
            # 关键词密度高，可能是部分匹配
            region = _locate_keyword_region(
                page, chunk_keywords, page_num, chunk_text
            )
            if region and region['similarity'] >= similarity_threshold * 0.8:
                results.append(region)
    
    doc.close()
    
    # 按相似度排序
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 去重相近的区域
    results = _remove_duplicate_regions(results)
    
    print(f"长文本匹配找到 {len(results)} 个候选区域")
    
    # 根据参数决定返回结果
    if return_best_only and results:
        print(f"返回最佳匹配: 相似度 {results[0]['similarity']:.3f}")
        return [results[0]]
    
    return results


def _extract_short_text_keywords(text: str) -> List[str]:
    """为短文本提取关键词 - 更简单的策略"""
    # 短文本直接使用有意义的词汇
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', text)
    
    # 过滤常见停用词
    stopwords = {'的', '和', '或', '及', '与', '对', '从', '在', '为', '是', '了', '到', '由', '有', '被', '所', '等', '这', '那', '一个', '可以', '应该'}
    keywords = [word for word in words if word not in stopwords and len(word) >= 2]
    
    # 短文本保留更多关键词
    return keywords[:10]


def _find_direct_text_matches(page, chunk_text: str, page_num: int) -> List[Dict[str, Any]]:
    """直接文本搜索匹配"""
    matches = []
    import pymupdf as fitz
    # 尝试找到包含部分文本的区域
    text_instances = page.search_for(chunk_text[:20])  # 搜索前20个字符
    
    for inst in text_instances:
        # 获取周围更大的文本区域
        expanded_rect = fitz.Rect(
            inst.x0 - 50, inst.y0 - 20, 
            inst.x1 + 200, inst.y1 + 100
        )
        
        # 确保在页面范围内
        page_rect = page.rect
        expanded_rect = expanded_rect & page_rect
        
        region_text = page.get_textbox(expanded_rect)
        similarity = _calculate_similarity(chunk_text, _clean_text(region_text))
        
        if similarity > 0.3:  # 较低的阈值
            matches.append({
                "page": page_num + 1,
                "bbox": [expanded_rect.x0, expanded_rect.y0, expanded_rect.x1, expanded_rect.y1],
                "type": "direct_text_match",
                "found_text": region_text[:150] + "..." if len(region_text) > 150 else region_text,
                "similarity": similarity,
                "match_type": "直接文本匹配"
            })
    
    return matches


def _find_keyword_matches(page, keywords: List[str], chunk_text: str, page_num: int, threshold: float) -> List[Dict[str, Any]]:
    """基于关键词的匹配"""
    matches = []
    
    if not keywords:
        return matches
    import pymupdf as fitz
    # 搜索主要关键词
    main_keyword = keywords[0] if keywords else ""
    if len(main_keyword) >= 3:
        keyword_instances = page.search_for(main_keyword)
        
        for inst in keyword_instances:
            # 扩展搜索区域
            expanded_rect = fitz.Rect(
                inst.x0 - 30, inst.y0 - 30,
                inst.x1 + 150, inst.y1 + 80
            )
            
            page_rect = page.rect
            expanded_rect = expanded_rect & page_rect
            
            region_text = page.get_textbox(expanded_rect)
            similarity = _calculate_similarity(chunk_text, _clean_text(region_text))
            
            if similarity >= threshold:
                matches.append({
                    "page": page_num + 1,
                    "bbox": [expanded_rect.x0, expanded_rect.y0, expanded_rect.x1, expanded_rect.y1],
                    "type": "keyword_match",
                    "found_text": region_text[:150] + "..." if len(region_text) > 150 else region_text,
                    "similarity": similarity,
                    "match_type": "关键词匹配",
                    "matched_keyword": main_keyword
                })
    
    return matches


def _find_fuzzy_matches(page, chunk_text: str, page_num: int, threshold: float) -> List[Dict[str, Any]]:
    """模糊匹配 - 逐段落搜索"""
    matches = []
    
    # 获取页面所有文本块
    text_dict = page.get_text("dict")
    text_blocks = []
    
    for block in text_dict["blocks"]:
        if block.get("type") == 0:  # 文本块
            block_text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    block_text += span["text"] + " "
            
            if block_text.strip():
                text_blocks.append({
                    "text": _clean_text(block_text),
                    "bbox": block["bbox"]
                })
    
    # 逐块检查相似度
    for block in text_blocks:
        similarity = _calculate_similarity(chunk_text, block["text"])
        
        if similarity >= threshold:
            matches.append({
                "page": page_num + 1,
                "bbox": block["bbox"],
                "type": "fuzzy_match",
                "found_text": block["text"][:150] + "..." if len(block["text"]) > 150 else block["text"],
                "similarity": similarity,
                "match_type": "模糊匹配"
            })
    
    return matches


def _process_short_text_results(results: List[Dict[str, Any]], return_best_only: bool) -> List[Dict[str, Any]]:
    """处理短文本匹配结果"""
    if not results:
        return results
    
    # 按相似度排序
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 去重
    results = _remove_duplicate_regions(results)
    
    # 短文本优先返回相似度最高的
    if return_best_only and results:
        return [results[0]]
    
    return results[:5]  # 短文本最多返回5个结果


def _clean_text(text: str) -> str:
    """清理和标准化文本"""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符但保留基本标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}""\'\'-]', ' ', text)
    return text.strip()


def _split_into_sentences(text: str) -> List[str]:
    """将文本分割成句子"""
    # 使用多种标点符号分割
    sentences = re.split(r'[.!?。！？；;]\s*', text)
    # 过滤掉太短的句子
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    return sentences


def _extract_page_content(page) -> Dict[str, Any]:
    """提取页面的所有内容"""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            return {}
    
    # 获取文本块信息
    text_dict = page.get_text("dict")
    
    content = {
        "text_blocks": [],
        "images": [],
        "tables": [],
        "page_size": {"width": page.rect.width, "height": page.rect.height}
    }
    
    # 处理文本块
    for block in text_dict["blocks"]:
        if block.get("type") == 0:  # 文本块
            block_text = ""
            block_bbox = block["bbox"]
            
            for line in block["lines"]:
                for span in line["spans"]:
                    block_text += span["text"] + " "
            
            if block_text.strip():
                content["text_blocks"].append({
                    "text": _clean_text(block_text),
                    "bbox": block_bbox,
                    "raw_text": block_text
                })
        
        elif block.get("type") == 1:  # 图像块
            content["images"].append({
                "bbox": block["bbox"],
                "width": block.get("width", 0),
                "height": block.get("height", 0)
            })
    
    # 检测表格（简单版本）
    drawings = page.get_drawings()
    table_areas = _detect_table_areas(drawings)
    
    for table_area in table_areas:
        table_text = page.get_textbox(fitz.Rect(table_area))
        if table_text.strip():
            content["tables"].append({
                "bbox": table_area,
                "text": _clean_text(table_text),
                "raw_text": table_text
            })
    
    return content


def _detect_table_areas(drawings) -> List[List[float]]:
    """简单的表格检测"""
    lines = []
    rects = []
    
    for drawing in drawings:
        if drawing.get("type") == "l":  # 线条
            items = drawing.get("items", [])
            for item in items:
                if item[0] == "l":  # line
                    lines.append(item[1:])  # [x0, y0, x1, y1]
        elif drawing.get("type") == "re":  # 矩形
            rect = drawing.get("rect", [])
            if len(rect) == 4:
                rects.append(rect)
    
    # 如果有足够多的线条或矩形，认为可能是表格
    if len(lines) > 5 or len(rects) > 3:
        all_coords = lines + rects
        if all_coords:
            min_x = min(coord[0] for coord in all_coords)
            min_y = min(coord[1] for coord in all_coords)
            max_x = max(coord[2] for coord in all_coords)
            max_y = max(coord[3] for coord in all_coords)
            
            return [[min_x, min_y, max_x, max_y]]
    
    return []


def _locate_best_region_in_page(page, chunk_text: str, keywords: List[str], 
                               page_num: int) -> Optional[Dict[str, Any]]:
    """在页面中定位最佳匹配区域"""
    
    # 获取文本块信息
    text_dict = page.get_text("dict")
    
    best_match = None
    best_similarity = 0
    best_bbox = None
    
    # 组合相邻的文本块来形成更大的文本区域
    text_regions = _group_text_blocks(text_dict["blocks"])
    
    for region in text_regions:
        region_text = _clean_text(region["text"])
        similarity = _calculate_similarity(chunk_text, region_text)
        
        # 额外考虑关键词匹配度
        keyword_score = _calculate_keyword_density(keywords, region_text)
        combined_score = similarity * 0.7 + keyword_score * 0.3
        
        if combined_score > best_similarity:
            best_similarity = combined_score
            best_match = region_text
            best_bbox = region["bbox"]
    
    if best_match and best_similarity > 0.3:
        return {
            "page": page_num + 1,
            "bbox": best_bbox,
            "type": "best_region_match",
            "found_text": best_match[:200] + "..." if len(best_match) > 200 else best_match,
            "similarity": best_similarity,
            "match_type": "整体区域匹配"
        }
    
    return None


def _group_text_blocks(blocks) -> List[Dict[str, Any]]:
    """将相邻的文本块组合成更大的文本区域"""
    text_blocks = []
    
    # 提取所有文本块
    for block in blocks:
        if block.get("type") == 0:  # 文本块
            block_text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    block_text += span["text"] + " "
            
            if block_text.strip():
                text_blocks.append({
                    "text": block_text.strip(),
                    "bbox": block["bbox"]
                })
    
    if not text_blocks:
        return []
    
    # 按Y坐标排序
    text_blocks.sort(key=lambda x: x["bbox"][1])
    
    # 组合相邻的文本块
    regions = []
    current_region = {
        "text": text_blocks[0]["text"],
        "bbox": list(text_blocks[0]["bbox"])
    }
    
    for i in range(1, len(text_blocks)):
        prev_bbox = current_region["bbox"]
        curr_bbox = text_blocks[i]["bbox"]
        
        # 如果垂直距离小于50，认为是同一区域
        vertical_gap = curr_bbox[1] - prev_bbox[3]
        
        if vertical_gap < 50:
            # 合并到当前区域
            current_region["text"] += " " + text_blocks[i]["text"]
            # 扩展边界框
            current_region["bbox"][0] = min(current_region["bbox"][0], curr_bbox[0])
            current_region["bbox"][1] = min(current_region["bbox"][1], curr_bbox[1])
            current_region["bbox"][2] = max(current_region["bbox"][2], curr_bbox[2])
            current_region["bbox"][3] = max(current_region["bbox"][3], curr_bbox[3])
        else:
            # 保存当前区域，开始新区域
            regions.append(current_region)
            current_region = {
                "text": text_blocks[i]["text"],
                "bbox": list(curr_bbox)
            }
    
    # 添加最后一个区域
    regions.append(current_region)
    
    return regions


def _locate_keyword_region(page, keywords: List[str], page_num: int, 
                          chunk_text: str) -> Optional[Dict[str, Any]]:
    """基于关键词密度定位区域"""
    
    text_dict = page.get_text("dict")
    text_regions = _group_text_blocks(text_dict["blocks"])
    
    best_region = None
    best_score = 0
    
    for region in text_regions:
        region_text = _clean_text(region["text"])
        keyword_density = _calculate_keyword_density(keywords, region_text)
        
        if keyword_density > best_score:
            best_score = keyword_density
            best_region = region
    
    if best_region and best_score > 0.2:
        # 计算与原文的相似度
        similarity = _calculate_similarity(chunk_text, _clean_text(best_region["text"]))
        
        return {
            "page": page_num + 1,
            "bbox": best_region["bbox"],
            "type": "keyword_region_match",
            "found_text": best_region["text"][:200] + "..." if len(best_region["text"]) > 200 else best_region["text"],
            "similarity": similarity,
            "keyword_density": best_score,
            "match_type": "关键词区域匹配"
        }
    
    return None


def _extract_key_phrases(text: str) -> List[str]:
    """提取关键短语和词汇"""
    # 去除标点符号和数字，保留有意义的词汇
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{2,}', text)
    
    # 过滤掉过短的词和常见停用词
    stopwords = {'的', '和', '或', '及', '与', '对', '从', '在', '为', '是', '了', '到', '由', '有', '被', '所', '等'}
    keywords = [word for word in words if len(word) >= 2 and word not in stopwords]
    
    # 去重并按长度排序（优先长词）
    keywords = list(set(keywords))
    keywords.sort(key=len, reverse=True)
    
    return keywords[:20]  # 返回前20个关键词


def _calculate_keyword_density(keywords: List[str], text: str) -> float:
    """计算关键词在文本中的密度"""
    if not keywords or not text:
        return 0
    
    text_lower = text.lower()
    matched_keywords = 0
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched_keywords += 1
    
    return matched_keywords / len(keywords)


def _remove_duplicate_regions(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去除重复或重叠的区域"""
    if len(results) <= 1:
        return results
    
    filtered = []
    
    for result in results:
        is_duplicate = False
        
        for existing in filtered:
            # 检查是否是同一页的重叠区域
            if result["page"] == existing["page"]:
                overlap = _calculate_bbox_overlap(result["bbox"], existing["bbox"])
                if overlap > 0.5:  # 50%以上重叠认为是重复
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            filtered.append(result)
    
    return filtered


def _calculate_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    # 使用序列匹配器计算相似度
    matcher = SequenceMatcher(None, text1.lower(), text2.lower())
    similarity = matcher.ratio()
    
    # 如果一个文本包含另一个文本，给予额外加分
    if text1.lower() in text2.lower() or text2.lower() in text1.lower():
        similarity = max(similarity, 0.8)
    
    return similarity


def _calculate_bbox_overlap(bbox1: List[float], bbox2: List[float]) -> float:
    """计算两个边界框的重叠比例"""
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # 计算交集
    intersection_x_min = max(x1_min, x2_min)
    intersection_y_min = max(y1_min, y2_min)
    intersection_x_max = min(x1_max, x2_max)
    intersection_y_max = min(y1_max, y2_max)
    
    if intersection_x_min >= intersection_x_max or intersection_y_min >= intersection_y_max:
        return 0  # 无交集
    
    intersection_area = (intersection_x_max - intersection_x_min) * (intersection_y_max - intersection_y_min)
    
    # 计算并集
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = area1 + area2 - intersection_area
    
    return intersection_area / union_area if union_area > 0 else 0


def _clean_text(text: str) -> str:
    """清理和标准化文本"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    # 移除一些特殊字符，但保留中英文和基本标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：、]', ' ', text)
    # 再次清理空白
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def _split_into_sentences(text: str) -> List[str]:
    """将文本分割成句子"""
    # 按标点符号分割
    sentences = re.split(r'[。！？\.\!\?]+', text)
    # 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def _calculate_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    if not text1 or not text2:
        return 0.0
    
    # 使用序列匹配器计算相似度
    matcher = SequenceMatcher(None, text1.lower(), text2.lower())
    return matcher.ratio()


def analyze_chunk_content(chunk_text: str) -> Dict[str, Any]:
    """分析知识切片的内容特征"""
    analysis = {
        "length": len(chunk_text),
        "sentences": len(_split_into_sentences(chunk_text)),
        "has_numbers": bool(re.search(r'\d+', chunk_text)),
        "has_punctuation": bool(re.search(r'[.!?。！？]', chunk_text)),
        "language_detected": "mixed",  # 简化版本
        "complexity_score": 0.0
    }
    
    # 计算复杂度分数
    complexity_factors = [
        len(chunk_text) / 1000,  # 长度因子
        analysis["sentences"] / 10,  # 句子数量因子
        len(re.findall(r'[,;:]', chunk_text)) / 20,  # 标点复杂度
    ]
    
    analysis["complexity_score"] = min(sum(complexity_factors), 1.0)
    
    return analysis


# 演示和测试函数
def demo_rag_locator():
    """演示RAG切片定位功能"""
    try:
        import pymupdf as fitz
    except ImportError:
        print("需要安装PyMuPDF来运行演示")
        return
    
    # 创建测试PDF
    doc = fitz.open()
    page = doc.new_page()
    
    # 添加复杂内容模拟RAG切片场景
    content_blocks = [
        "人工智能（Artificial Intelligence，AI）是指由人制造出来的机器所表现出来的智能。",
        "通常人工智能是指通过普通计算机程序来呈现人类智能的技术。",
        "",  # 空行
        "机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习。",
        "深度学习则是机器学习的一个子集，使用多层神经网络来处理复杂的数据模式。",
    ]
    
    y_pos = 100
    for block in content_blocks:
        if block:  # 非空行
            page.insert_text((50, y_pos), block, fontsize=12)
        y_pos += 25
    
    # 添加表格
    table_y = 250
    page.draw_rect(fitz.Rect(50, table_y, 450, table_y + 100), width=1)
    
    # 表格内容
    headers = ["技术", "应用领域", "发展阶段"]
    data = [
        ["机器学习", "数据分析", "成熟"],
        ["深度学习", "图像识别", "快速发展"],
    ]
    
    # 绘制表格
    for i, header in enumerate(headers):
        page.insert_text((70 + i * 120, table_y + 20), header, fontsize=10)
    
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            page.insert_text((70 + j * 120, table_y + 40 + i * 25), cell, fontsize=10)
    
    test_pdf = "rag_test.pdf"
    doc.save(test_pdf)
    doc.close()
    print(f"RAG测试PDF已创建: {test_pdf}")
    
    # 模拟RAG知识切片
    rag_chunks = [
        # 切片1：单段文本
        "人工智能是指由人制造出来的机器所表现出来的智能。通常人工智能是指通过普通计算机程序来呈现人类智能的技术。",
        
        # 切片2：多段文本
        "机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习。深度学习则是机器学习的一个子集，使用多层神经网络来处理复杂的数据模式。",
        
        # 切片3：部分文本
        "深度学习则是机器学习的一个子集",
        
        # 切片4：包含表格信息的文本
        "机器学习在数据分析领域应用广泛，目前发展已经相对成熟。"
    ]
    
    print("\n开始定位RAG知识切片...")
    
    for i, chunk in enumerate(rag_chunks, 1):
        print(f"\n--- 切片 {i} ---")
        print(f"内容: {chunk[:100]}...")
        
        # 分析切片特征
        analysis = analyze_chunk_content(chunk)
        print(f"分析: 长度={analysis['length']}, 句子数={analysis['sentences']}, 复杂度={analysis['complexity_score']:.2f}")
        
        # 定位切片
        results = find_rag_chunk_coordinates(chunk, test_pdf, similarity_threshold=0.4)
        
        if results:
            print(f"找到 {len(results)} 个匹配位置:")
            for j, result in enumerate(results, 1):
                print(f"  {j}. 页码: {result['page']}")
                print(f"     坐标: {result['bbox']}")
                print(f"     类型: {result['type']}")
                print(f"     相似度: {result['similarity']:.3f}")
                
                if result['type'] == 'combined_match':
                    print(f"     覆盖区域: {result['coverage_area']['width']:.1f} x {result['coverage_area']['height']:.1f}")
                    print(f"     包含部分: {result['chunk_parts']}")
        else:
            print("未找到匹配位置")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        chunk_content = sys.argv[1]
        pdf_file = sys.argv[2]
        
        # 可选参数
        similarity_threshold = 0.6
        if len(sys.argv) > 3:
            try:
                similarity_threshold = float(sys.argv[3])
            except ValueError:
                print("相似度阈值必须是0-1之间的数字")
                sys.exit(1)
        
        print(f"在PDF '{pdf_file}' 中定位知识切片")
        print(f"相似度阈值: {similarity_threshold}")
        print(f"切片内容: {chunk_content[:100]}...")
        
        # 分析切片
        analysis = analyze_chunk_content(chunk_content)
        print(f"\n切片分析:")
        print(f"- 长度: {analysis['length']} 字符")
        print(f"- 句子数: {analysis['sentences']}")
        print(f"- 复杂度: {analysis['complexity_score']:.2f}")
        
        # 定位切片
        results = find_rag_chunk_coordinates(chunk_content, pdf_file, similarity_threshold)
        
        if results:
            print(f"\n找到 {len(results)} 个匹配位置:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 页码: {result['page']}")
                print(f"   坐标: {result['bbox']}")
                print(f"   类型: {result['type']}")
                print(f"   相似度: {result['similarity']:.3f}")
                
                if result['type'] == 'combined_match':
                    print(f"   覆盖区域: {result['coverage_area']['width']:.1f} x {result['coverage_area']['height']:.1f}")
                    print(f"   包含部分: {result['chunk_parts']}")
                    print(f"   匹配句子数: {len(result['matched_sentences'])}")
                
                # 保存详细结果到JSON
                output_file = f"rag_chunk_location_{i}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"   详细结果已保存: {output_file}")
        else:
            print("未找到匹配的位置")
            print("建议:")
            print("- 降低相似度阈值（当前: {:.2f}）".format(similarity_threshold))
            print("- 检查切片内容是否确实在PDF中")
            print("- 切片可能跨页或格式差异较大")
    
    else:
        print("RAG知识切片坐标定位器演示")
        print("=" * 50)
        demo_rag_locator()
        print("\n" + "=" * 50)
        print("用法:")
        print("python rag_chunk_locator.py '知识切片内容' 'pdf文件路径' [相似度阈值]")
        print("相似度阈值范围: 0.0-1.0，默认0.6，越低匹配越宽松") 