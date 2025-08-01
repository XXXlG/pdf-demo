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
    对文本进行数据清洗，去除特殊符号和多余空格
    
    Args:
        text: 原始文本
        
    Returns:
        清洗后的文本
    """
    # 移除多余的空白字符和换行符
    text = re.sub(r'\s+', ' ', text)
    
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


def mineru_chunk_locate(filename: str, text: str, similarity_threshold: float = 0.6) -> Dict[str, Any]:
    """
    根据文本匹配其在全文中的坐标和页码索引
    
    Args:
        filename: 文件名（不含扩展名）
        text: 待匹配的文本
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
    
    for page_idx, page_info in enumerate(pdf_info):
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
                            "index": int(block.get('index', 0))  # 确保index是整数
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
                bbox_overlap_ratio(match['bbox'], existing['bbox']) > 0.8):
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
    x0 = min(bbox[0] for bbox in all_bboxes)
    y0 = min(bbox[1] for bbox in all_bboxes)
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