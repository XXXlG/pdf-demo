#!/usr/bin/env python3
"""
MinerU格式文本坐标定位器
根据文本匹配其在全文中的坐标和页码索引
"""

import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from pathlib import Path


def clean_text_for_matching(text: str) -> str:
    """
    对文本进行数据清洗，去除特殊符号、图片URL和多余空格
    
    Args:
        text: 原始文本
        
    Returns:
        清洗后的文本
    """
    # 移除多余的空白字符和换行符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除图片URL（包括http和https协议的图片链接）
    image_url_pattern = r'https?://[^\s]*\.(jpg|jpeg|png|gif|bmp|webp|svg|tiff?|ico)(\?[^\s]*)?#'
    text = re.sub(image_url_pattern, '', text, flags=re.IGNORECASE)
    
    # 移除特殊符号，保留中英文、数字和基本标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}""\'\'-]', '', text)
    
    # 移除多余空格
    text = re.sub(r'\s+', '', text)
    
    return text.strip()


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度分数(0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # 清洗文本
    clean_text1 = clean_text_for_matching(text1)
    clean_text2 = clean_text_for_matching(text2)
    
    if not clean_text1 or not clean_text2:
        return 0.0
    
    # 使用SequenceMatcher计算相似度
    similarity = SequenceMatcher(None, clean_text1, clean_text2).ratio()
    
    return similarity


def load_middle_json(filename: str) -> Optional[Dict]:
    """
    加载指定的middle.json文件
    
    Args:
        filename: 文件名（不含扩展名）
        
    Returns:
        JSON数据或None
    """
    data_dir = Path("./data")
    json_path = data_dir / f"{filename}_middle.json"
    
    if not json_path.exists():
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败: {e}")
        return None


def extract_text_from_para_block(para_block: Dict) -> str:
    """
    从para_block中提取文本内容
    
    Args:
        para_block: 文本块数据
        
    Returns:
        提取的文本内容
    """
    if para_block.get('type') != 'text':
        return ""
    
    text_parts = []
    lines = para_block.get('lines', [])
    
    for line in lines:
        spans = line.get('spans', [])
        for span in spans:
            content = span.get('content', '')
            if content:
                text_parts.append(content)
    
    return ''.join(text_parts)


def find_continuous_blocks(para_blocks: List[Dict], start_idx: int, target_text: str, 
                          similarity_threshold: float = 0.6) -> Tuple[List[Dict], float]:
    """
    从指定位置开始查找连续的匹配文本块
    
    Args:
        para_blocks: 文本块列表
        start_idx: 开始索引
        target_text: 目标文本
        similarity_threshold: 相似度阈值
        
    Returns:
        (匹配的连续文本块列表, 总体相似度分数)
    """
    if start_idx >= len(para_blocks):
        return [], 0.0
    
    matched_blocks = []
    combined_text = ""
    target_clean = clean_text_for_matching(target_text)
    
    # 从start_idx开始，尝试连续匹配
    for i in range(start_idx, len(para_blocks)):
        block = para_blocks[i]
        if block.get('type') != 'text':
            continue
        
        block_text = extract_text_from_para_block(block)
        if not block_text:
            continue
        
        # 将当前块加入候选
        test_combined = combined_text + clean_text_for_matching(block_text)
        test_similarity = calculate_text_similarity(target_clean, test_combined)
        
        # 如果加入当前块后相似度提高，则加入
        if test_similarity > similarity_threshold or (matched_blocks and test_similarity >= 0.3):
            matched_blocks.append(block)
            combined_text = test_combined
        else:
            # 如果相似度太低且已有匹配块，则停止
            if matched_blocks:
                break
    
    # 计算最终相似度
    final_similarity = calculate_text_similarity(target_clean, combined_text) if combined_text else 0.0
    
    return matched_blocks, final_similarity


def mineru_chunk_locate(filename: str, text: str, similarity_threshold: float = 0.6, page_number: Optional[int] = None) -> Dict[str, Any]:
    """
    根据文本匹配其在全文中的坐标和页码索引
    
    Args:
        filename: 文件名（不含扩展名）
        text: 待匹配的文本
        similarity_threshold: 相似度阈值
        page_number: 起始页面索引（从0开始），如果为None则从第0页开始搜索
        
    Returns:
        匹配结果字典
    """
    # 1. 数据清洗
    cleaned_text = clean_text_for_matching(text)
    if not cleaned_text:
        return {
            "success": False,
            "message": "输入文本为空或无效",
            "results": []
        }
    if(len(cleaned_text)<100):similarity_threshold = 0.8; #短文本支持 高精度匹配
    # 2. 加载middle.json文件
    json_data = load_middle_json(filename)
    if not json_data:
        return {
            "success": False,
            "message": f"未找到文件: {filename}_middle.json",
            "results": []
        }
    
    pdf_info = json_data.get('pdf_info', [])
    if not pdf_info:
        return {
            "success": False,
            "message": "JSON文件格式错误：未找到pdf_info",
            "results": []
        }
    
    # 3. 遍历所有页面，查找匹配的para_blocks
    all_matches = []
    
    # 确定起始页面索引
    start_page = page_number if page_number is not None else 0
    if start_page >= len(pdf_info):
        return {
            "success": False,
            "message": f"指定的起始页面索引 {start_page} 超出了文档总页数 {len(pdf_info)}",
            "results": []
        }
    
    for page_idx, page_info in enumerate(pdf_info):
        # 跳过指定页面之前的页面
        if page_idx < start_page:
            continue
        para_blocks = page_info.get('para_blocks', [])
        page_size = page_info.get('page_size', [0, 0])
        
        # 筛选type为text的块
        text_blocks = [block for block in para_blocks if block.get('type') == 'text']
        
        if not text_blocks:
            continue
        
        # 遍历每个文本块作为起始点，寻找连续匹配
        for start_idx, start_block in enumerate(text_blocks):
            start_text = extract_text_from_para_block(start_block)
            if not start_text:
                continue
            
            # 快速预检查：如果起始块就不包含目标文本的关键词，跳过
            start_clean = clean_text_for_matching(start_text)
            if len(cleaned_text) > 50:  # 长文本检查关键词重叠
                # 提取目标文本的关键词（简单方法：取前面的字符）
                key_chars = cleaned_text[:20] if len(cleaned_text) >= 20 else cleaned_text
                if not any(char in start_clean for char in key_chars[:5]):
                    continue
            
            # 查找从当前块开始的连续匹配
            matched_blocks, similarity = find_continuous_blocks(
                text_blocks, start_idx, text, similarity_threshold
            )
            
            if matched_blocks and similarity >= similarity_threshold:
                # 计算合并后的边界框
                combined_bbox = calculate_combined_bbox(matched_blocks)
                
                # 提取匹配的文本预览
                matched_text = ""
                for block in matched_blocks:
                    matched_text += extract_text_from_para_block(block)
                
                match_result = {
                    "page_idx": page_idx,
                    "page_size": page_size,
                    "bbox": combined_bbox,
                    "similarity": round(similarity, 3),
                    "block_count": len(matched_blocks),
                    "matched_text_preview": matched_text[:200] + "..." if len(matched_text) > 200 else matched_text,
                    "block_details": [
                        {
                            "bbox": block.get('bbox', []),
                            "bbox_fs": block.get('bbox_fs', []),
                            "index": int(block.get('index', 0)),  # 确保index是整数
                            "source_page_idx": page_idx  # 添加文本块所在的页码
                        }
                        for block in matched_blocks
                    ]
                }
                
                all_matches.append(match_result)
    
    # 4. 按相似度排序并去重
    all_matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 简单去重：移除重叠度很高的结果
    unique_matches = []
    for match in all_matches:
        is_duplicate = False
        for existing in unique_matches:
            if (match['page_idx'] == existing['page_idx'] and 
                bbox_overlap_ratio(match['bbox'], existing['bbox']) > 0.65):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_matches.append(match)
    
    # 5. 返回结果
    if unique_matches:
        return {
            "success": True,
            "message": f"找到 {len(unique_matches)} 个匹配区域",
            "query_text": text,
            "cleaned_text": cleaned_text,
            "similarity_threshold": similarity_threshold,
            "results": unique_matches[:10]  # 最多返回10个结果
        }
    else:
        return {
            "success": False,
            "message": "未找到匹配的文本区域，建议降低相似度阈值",
            "query_text": text,
            "cleaned_text": cleaned_text,
            "similarity_threshold": similarity_threshold,
            "results": []
        }


def calculate_combined_bbox(blocks: List[Dict]) -> List[float]:
    """
    计算多个文本块的合并边界框
    
    Args:
        blocks: 文本块列表
        
    Returns:
        合并后的边界框 [x0, y0, x1, y1]
    """
    if not blocks:
        return [0, 0, 0, 0]
    
    all_bboxes = []
    for block in blocks:
        bbox = block.get('bbox') or block.get('bbox_fs')
        if bbox and len(bbox) >= 4:
            all_bboxes.append(bbox)
    
    if not all_bboxes:
        return [0, 0, 0, 0]
    
    # 计算最小外接矩形
    x0 = max(bbox[0] for bbox in all_bboxes)
    y0 = max(bbox[1] for bbox in all_bboxes)
    x1 = max(bbox[2] for bbox in all_bboxes)
    y1 = max(bbox[3] for bbox in all_bboxes)
    
    return [x0, y0, x1, y1]


def bbox_overlap_ratio(bbox1: List[float], bbox2: List[float]) -> float:
    """
    计算两个边界框的重叠比例
    
    Args:
        bbox1: 边界框1 [x0, y0, x1, y1]
        bbox2: 边界框2 [x0, y0, x1, y1]
        
    Returns:
        重叠比例 (0-1)
    """
    if len(bbox1) < 4 or len(bbox2) < 4:
        return 0.0
    
    # 计算交集
    x0 = max(bbox1[0], bbox2[0])
    y0 = max(bbox1[1], bbox2[1])
    x1 = min(bbox1[2], bbox2[2])
    y1 = min(bbox1[3], bbox2[3])
    
    if x1 <= x0 or y1 <= y0:
        return 0.0  # 没有交集
    
    # 交集面积
    intersection = (x1 - x0) * (y1 - y0)
    
    # 各自面积
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    
    # 并集面积
    union = area1 + area2 - intersection
    
    if union <= 0:
        return 0.0
    
    return intersection / union


def header_chunk_locate(filename: str, text: str, page_number: int, similarity_threshold: float = 0.6) -> Dict[str, Any]:
    """
    在指定页码中定位文本，通过匹配开头30%和结尾30%的文本来确定整体坐标范围
    
    Args:
        filename: 文件名（不含扩展名）
        text: 待匹配的文本
        page_number: 指定的页码索引（从0开始）
        similarity_threshold: 相似度阈值
        
    Returns:
        匹配结果字典
    """
    # 1. 数据清洗
    cleaned_text = clean_text_for_matching(text)
    if not cleaned_text:
        return {
            "success": False,
            "message": "输入文本为空或无效",
            "results": []
        }
    
    # 2. 截取开头30%和结尾30%的文本
    text_length = len(cleaned_text)
    start_portion_length = max(20, int(text_length * 0.1))  # 至少20个字符
    end_portion_length = max(20, int(text_length * 0.1))    # 至少20个字符
    
    start_text = cleaned_text[:start_portion_length]
    end_text = cleaned_text[-end_portion_length:]
    
    # 短文本支持高精度匹配
    if len(cleaned_text) < 100:
        similarity_threshold = 0.5
    
    # 3. 加载middle.json文件
    json_data = load_middle_json(filename)
    if not json_data:
        return {
            "success": False,
            "message": f"未找到文件: {filename}_middle.json",
            "results": []
        }
    
    pdf_info = json_data.get('pdf_info', [])
    if not pdf_info:
        return {
            "success": False,
            "message": "JSON文件格式错误：未找到pdf_info",
            "results": []
        }
    
    # 4. 验证指定页码范围是否存在
    start_page = page_number
    end_page = min(page_number + 4, len(pdf_info) - 1)  # 最多查找5页，不超过文档总页数
    
    if start_page < 0 or start_page >= len(pdf_info):
        return {
            "success": False,
            "message": f"指定的起始页码 {start_page} 超出文档范围（总页数: {len(pdf_info)}）",
            "results": []
        }
    
    # 5. 在指定页码范围内收集所有text_blocks
    all_text_blocks = []
    page_ranges = []
    
    for current_page_idx in range(start_page, end_page + 1):
        page_info = pdf_info[current_page_idx]
        para_blocks = page_info.get('para_blocks', [])
        page_size = page_info.get('page_size', [0, 0])
        
        # 筛选type为text的块，并记录页面信息
        page_text_blocks = []
        for block in para_blocks:
            if block.get('type') == 'text':
                # 为每个文本块添加页面信息
                block_with_page = block.copy()
                block_with_page['source_page_idx'] = current_page_idx
                block_with_page['source_page_size'] = page_size
                page_text_blocks.append(block_with_page)
        
        all_text_blocks.extend(page_text_blocks)
        page_ranges.append({
            'page_idx': current_page_idx,
            'page_size': page_size,
            'block_count': len(page_text_blocks)
        })
    
    if not all_text_blocks:
        return {
            "success": False,
            "message": f"第 {start_page} 到 {end_page} 页中未找到文本块",
            "results": []
        }
    
    # 6. 分别查找开头30%和结尾30%的文本（在多页范围内）
    start_match = find_text_segment_in_pages(all_text_blocks, start_text, similarity_threshold)
    end_match = find_text_segment_in_pages(all_text_blocks, end_text, similarity_threshold)
    
    # 7. 分析匹配结果
    if start_match and end_match:
        # 获取开始和结束匹配的页面信息
        start_pages = start_match.get('page_idx', [])
        end_pages = end_match.get('page_idx', [])
        
        # 确定开始和结束页面索引
        start_page_idx = start_pages if isinstance(start_pages, int) else start_pages[0]
        end_page_idx = end_pages if isinstance(end_pages, int) else end_pages[0]
        
        # 检查是否在同一页面
        if start_page_idx == end_page_idx:
            # 同一页面，使用原有逻辑
            start_bbox = start_match['bbox']
            end_bbox = end_match['bbox']
            
            # 计算合并后的大边界框
            combined_bbox = [
                min(start_bbox[0], end_bbox[0]),  # 最小x
                min(start_bbox[1], end_bbox[1]),  # 最小y
                max(start_bbox[2], end_bbox[2]),  # 最大x
                max(start_bbox[3], end_bbox[3])   # 最大y
            ]
            
            # 合并所有相关的文本块
            all_blocks = start_match['blocks'] + end_match['blocks']
            # 去重（根据index）
            unique_blocks = []
            seen_indices = set()
            for block in all_blocks:
                block_index = block.get('index', 0)
                if block_index not in seen_indices:
                    unique_blocks.append(block)
                    seen_indices.add(block_index)
            
            # 提取匹配的文本预览
            matched_text = ""
            for block in unique_blocks:
                matched_text += extract_text_from_para_block(block)
            
            avg_similarity = (start_match['similarity'] + end_match['similarity']) / 2
            
            # 获取页面尺寸
            page_size = next(
                (pr['page_size'] for pr in page_ranges if pr['page_idx'] == start_page_idx),
                [0, 0]
            )
            
            match_result = {
                "cross_page_match": False,
                "page_idx": start_page_idx,
                "page_size": page_size,
                "bbox": combined_bbox,
                "similarity": round(avg_similarity, 3),
                "block_count": len(unique_blocks),
                "matched_text_preview": matched_text[:200] + "..." if len(matched_text) > 200 else matched_text,
                "block_details": [
                    {
                        "bbox": block.get('bbox', []),
                        "bbox_fs": block.get('bbox_fs', []),
                        "index": int(block.get('index', 0)),
                        "source_page_idx": block.get('source_page_idx', start_page_idx)
                    }
                    for block in unique_blocks
                ],
                "match_info": {
                    "start_text": start_text[:50] + "..." if len(start_text) > 50 else start_text,
                    "end_text": end_text[:50] + "..." if len(end_text) > 50 else end_text,
                    "start_similarity": round(start_match['similarity'], 3),
                    "end_similarity": round(end_match['similarity'], 3),
                    "search_range": f"页面 {start_page} 到 {end_page}",
                    "cross_page": False
                }
            }
            
            # 同页匹配返回单个结果
            return {
                "success": True,
                "message": f"在页面 {start_page}-{end_page} 范围内成功定位文本区域（通过开头和结尾30%匹配）",
                "query_text": text,
                "cleaned_text": cleaned_text,
                "similarity_threshold": similarity_threshold,
                "results": [match_result]
            }
            
        else:
            # 跨页匹配，返回两个独立的匹配结果
            start_page_size = next(
                (pr['page_size'] for pr in page_ranges if pr['page_idx'] == start_page_idx),
                [0, 0]
            )
            end_page_size = next(
                (pr['page_size'] for pr in page_ranges if pr['page_idx'] == end_page_idx),
                [0, 0]
            )
            
            # 计算开始页面的区域：从匹配位置到页面底部
            start_bbox = start_match['bbox']
            start_region_bbox = [
                0,  # 左边界设为页面左边
                start_bbox[1],  # 上边界为匹配位置的上边界
                start_page_size[0],  # 右边界设为页面右边
                start_page_size[1]  # 下边界设为页面底部
            ]
            
            # 计算结束页面的区域：从页面顶部到匹配位置
            end_bbox = end_match['bbox']
            end_region_bbox = [
                0,  # 左边界设为页面左边
                0,  # 上边界设为页面顶部
                end_page_size[0],  # 右边界设为页面右边
                end_bbox[3]  # 下边界为匹配位置的下边界
            ]
            
            # 构建开始区域的block_details
            start_block_details = [
                {
                    "bbox": block.get('bbox', []),
                    "bbox_fs": block.get('bbox_fs', []),
                    "index": int(block.get('index', 0)),
                    "source_page_idx": block.get('source_page_idx', start_page_idx)
                }
                for block in start_match['blocks']
            ]
            
            # 构建结束区域的block_details
            end_block_details = [
                {
                    "bbox": block.get('bbox', []),
                    "bbox_fs": block.get('bbox_fs', []),
                    "index": int(block.get('index', 0)),
                    "source_page_idx": block.get('source_page_idx', end_page_idx)
                }
                for block in end_match['blocks']
            ]
            
            # 创建开始区域的匹配结果
            start_match_result = {
                "cross_page_match": True,
                "region_type": "start",
                "page_idx": start_page_idx,
                "page_size": start_page_size,
                "bbox": start_region_bbox,
                "similarity": round(start_match['similarity'], 3),
                "block_count": len(start_match['blocks']),
                "matched_text_preview": start_match.get('text', '')[:200] + "..." if len(start_match.get('text', '')) > 200 else start_match.get('text', ''),
                "block_details": start_block_details,
                "match_info": {
                    "start_text": start_text[:50] + "..." if len(start_text) > 50 else start_text,
                    "end_text": end_text[:50] + "..." if len(end_text) > 50 else end_text,
                    "start_similarity": round(start_match['similarity'], 3),
                    "end_similarity": round(end_match['similarity'], 3),
                    "search_range": f"页面 {start_page} 到 {end_page}",
                    "cross_page": True,
                    "region_type": "start"
                }
            }
            
            # 创建结束区域的匹配结果
            end_match_result = {
                "cross_page_match": True,
                "region_type": "end",
                "page_idx": end_page_idx,
                "page_size": end_page_size,
                "bbox": end_region_bbox,
                "similarity": round(end_match['similarity'], 3),
                "block_count": len(end_match['blocks']),
                "matched_text_preview": end_match.get('text', '')[:200] + "..." if len(end_match.get('text', '')) > 200 else end_match.get('text', ''),
                "block_details": end_block_details,
                "match_info": {
                    "start_text": start_text[:50] + "..." if len(start_text) > 50 else start_text,
                    "end_text": end_text[:50] + "..." if len(end_text) > 50 else end_text,
                    "start_similarity": round(start_match['similarity'], 3),
                    "end_similarity": round(end_match['similarity'], 3),
                    "search_range": f"页面 {start_page} 到 {end_page}",
                    "cross_page": True,
                    "region_type": "end"
                }
            }
            
            # 跨页匹配返回两个结果
            return {
                "success": True,
                "message": f"在页面 {start_page}-{end_page} 范围内成功定位跨页文本区域（通过开头和结尾30%匹配）",
                "query_text": text,
                "cleaned_text": cleaned_text,
                "similarity_threshold": similarity_threshold,
                "results": [start_match_result, end_match_result]
            }

        
    elif start_match:
        # 只找到开头部分
        # 使用新添加的page_idx信息
        start_pages = start_match.get('page_idx', start_page)
        match_page_idx = start_pages if isinstance(start_pages, int) else start_pages[0]
        match_page_size = next(
            (pr['page_size'] for pr in page_ranges if pr['page_idx'] == match_page_idx),
            [0, 0]
        )
        
        match_result = {
            "page_idx": match_page_idx,
            "page_size": match_page_size,
            "bbox": start_match['bbox'],
            "similarity": round(start_match['similarity'], 3),
            "block_count": len(start_match['blocks']),
            "matched_text_preview": start_match['text'][:200] + "..." if len(start_match['text']) > 200 else start_match['text'],
            "block_details": [
                {
                    "bbox": block.get('bbox', []),
                    "bbox_fs": block.get('bbox_fs', []),
                    "index": int(block.get('index', 0)),
                    "source_page_idx": block.get('source_page_idx', match_page_idx)
                }
                for block in start_match['blocks']
            ],
            "match_info": {
                "match_type": "start_only",
                "start_text": start_text[:50] + "..." if len(start_text) > 50 else start_text,
                "start_similarity": round(start_match['similarity'], 3),
                "search_range": f"页面 {start_page} 到 {end_page}"
            }
        }
        
        return {
            "success": True,
            "message": f"在页面 {start_page}-{end_page} 范围内找到文本开头部分",
            "query_text": text,
            "cleaned_text": cleaned_text,
            "similarity_threshold": similarity_threshold,
            "results": [match_result]
        }
        
    elif end_match:
        # 只找到结尾部分
        # 使用新添加的page_idx信息
        end_pages = end_match.get('page_idx', start_page)
        match_page_idx = end_pages if isinstance(end_pages, int) else end_pages[0]
        match_page_size = next(
            (pr['page_size'] for pr in page_ranges if pr['page_idx'] == match_page_idx),
            [0, 0]
        )
        
        match_result = {
            "page_idx": match_page_idx,
            "page_size": match_page_size,
            "bbox": end_match['bbox'],
            "similarity": round(end_match['similarity'], 3),
            "block_count": len(end_match['blocks']),
            "matched_text_preview": end_match['text'][:200] + "..." if len(end_match['text']) > 200 else end_match['text'],
            "block_details": [
                {
                    "bbox": block.get('bbox', []),
                    "bbox_fs": block.get('bbox_fs', []),
                    "index": int(block.get('index', 0)),
                    "source_page_idx": block.get('source_page_idx', match_page_idx)
                }
                for block in end_match['blocks']
            ],
            "match_info": {
                "match_type": "end_only", 
                "end_text": end_text[:50] + "..." if len(end_text) > 50 else end_text,
                "end_similarity": round(end_match['similarity'], 3),
                "search_range": f"页面 {start_page} 到 {end_page}"
            }
        }
        
        return {
            "success": True,
            "message": f"在页面 {start_page}-{end_page} 范围内找到文本结尾部分",
            "query_text": text,
            "cleaned_text": cleaned_text,
            "similarity_threshold": similarity_threshold,
            "results": [match_result]
        }
    
    else:
        return {
            "success": False,
            "message": f"在页面 {start_page}-{end_page} 范围内未找到匹配的文本区域（开头30%和结尾30%都未匹配），建议降低相似度阈值",
            "query_text": text,
            "cleaned_text": cleaned_text,
            "similarity_threshold": similarity_threshold,
            "results": []
        }


def find_text_segment_in_pages(text_blocks: List[Dict], target_text: str, threshold: float) -> Optional[Dict[str, Any]]:
    """
    在多个页面中查找文本片段的最佳匹配
    
    Args:
        text_blocks: 包含多页文本块的列表（每个块包含source_page_idx信息）
        target_text: 目标文本片段
        threshold: 相似度阈值
        
    Returns:
        匹配结果字典，包含bbox、blocks、similarity、text和page_idx，如果未找到返回None
        - bbox: 文本块的边界框坐标
        - blocks: 匹配的文本块列表
        - similarity: 文本相似度分数
        - text: 合并的文本内容
        - page_idx: 页面索引（单页时为整数，多页时为整数列表）
    """
    # 清洗目标文本
    target_cleaned = clean_text_for_matching(target_text)
    if not target_cleaned:
        return None
    
    best_match = None
    best_similarity = 0.0
    
    # 遍历所有可能的文本块组合
    for start_idx in range(len(text_blocks)):
        for end_idx in range(start_idx, len(text_blocks)):
            # 提取从start_idx到end_idx的所有文本
            combined_text = ""
            current_blocks = text_blocks[start_idx:end_idx + 1]
            
            for block in current_blocks:
                block_text = extract_text_from_para_block(block)
                if block_text:
                    combined_text += block_text
            
            if not combined_text:
                continue
            
            # 计算相似度
            combined_cleaned = clean_text_for_matching(combined_text)
            similarity = calculate_text_similarity(target_cleaned, combined_cleaned)
            
            # 更新最佳匹配
            if similarity >= threshold and similarity > best_similarity:
                # 计算这组文本块的合并边界框
                combined_bbox = calculate_combined_bbox(current_blocks)
                
                # 收集所有相关的页面信息
                page_indices = []
                for block in current_blocks:
                    page_idx = block.get('source_page_idx')
                    if page_idx is not None and page_idx not in page_indices:
                        page_indices.append(page_idx)
                
                # 如果只有一个页面，直接返回page_idx；如果跨多页，返回页面列表
                if len(page_indices) == 1:
                    page_info = page_indices[0]
                else:
                    page_info = sorted(page_indices)  # 多页时返回排序的页面列表
                
                best_match = {
                    'bbox': combined_bbox,
                    'blocks': current_blocks.copy(),
                    'similarity': similarity,
                    'text': combined_text,
                    'page_idx': page_info
                }
                best_similarity = similarity
            
            # 优化：如果文本长度已经远超目标文本，可以停止扩展
            if len(combined_cleaned) > len(target_cleaned) * 2:
                break
    
    return best_match