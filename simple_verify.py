#!/usr/bin/env python3
"""
简单的RAG匹配结果验证工具
"""

def manual_verify():
    """手动验证之前的匹配结果"""
    
    print("🔍 手动验证RAG匹配结果")
    print("=" * 50)
    
    # 之前的匹配结果
    match_result = {
        "page": 15,
        "bbox": [57.88999938964844, 30.45492935180664, 364.1160583496094, 544.4697265625],
        "similarity": 0.478,
        "match_type": "整体区域匹配"
    }
    
    # 原始切片内容
    original_chunk = """
1）元器件安装孔与元器件引线不匹配# 问题描述印制板元器件安装孔孔径与元器件引线直径不匹配，导致元器件引线无法安装或间隙过小，容易导致安装孔损伤或透锡不良，影响焊点的可靠性，见图1-1所示。  缺陷案例照片、图片  ![](http://192.168.0.130:94/images/1e601365186a9748addcb8ab93f6d8fc753fa7a003dd8c02158656e8ddf28386.jpg)  图1-1元器件引线直径与印制板元器件安装孔直径 间隙过小，容易损伤元器件安装孔缺陷案例照片、图片![](http://192.168.0.130:94/images/1e601365186a9748addcb8ab93f6d8fc753fa7a003dd8c02158656e8ddf28386.jpg)# 正确方法印制板元器件安装孔成孔公称直径与元器件引线公称直径之间应有 $0 . 2 { \sim } 0 . 4 ~ \mathrm { m m }$ 的径向间隙。# 依据文件、标准或规范QJ3012-98第5.5.1节规定：印制板元器件安装孔径与元器件引线之间，采用手工焊接工艺时应保持 $0 . 2 \sim 0 . 4 ~ \mathrm { m m }$ 的合理间隙，采用波峰焊工艺时应保持 $0 . 2 { \sim } 0 . 3 \ \mathrm { m m }$ 的合理间隙。当孔径与线径失配时，不允许采取扩孔和修配线径的办法。  QJ3013-99第5.3.4.4节规定：印制板钻孔公称直径与元器件引线公称直径的差值取 $0 . 2 \sim 0 . 4 \ \mathrm { m m }$ ，对于金属化孔，差值取$0 . 3 { \sim } 0 . 4 ~ \mathrm { m m }$ 。对于矩形引线，引线直径为矩形横接面的对角线，并且孔与矩形引线的间隙不大于矩形引线厚度方向尺寸的 $0 . 7 ~ \mathrm { m m }$ 。  GJB4057-2000第6.4.1.2节规定：镀覆孔的直径应比元器件引线的最大尺寸大 $0 . 2 { \sim } 0 . 4 ~ \mathrm { m m }$ 。  $\operatorname { E C S S - Q - 7 0 - 0 8 A }$ 第8.4.2节规定：镀通孔直径比元器件引线直径大 $0 . 3 { \sim } 0 . 6 5 ~ \mathrm { m m }$ 。元器件非镀通孔的直径比元器件引线直径最大不应超过 $0 . 2 ~ \mathrm { m m }$ 。
    """
    
    print(f"📄 匹配页码: {match_result['page']}")
    print(f"📍 匹配区域坐标: {match_result['bbox']}")
    print(f"📏 区域大小: {match_result['bbox'][2] - match_result['bbox'][0]:.0f} x {match_result['bbox'][3] - match_result['bbox'][1]:.0f} 像素")
    print(f"📊 相似度: {match_result['similarity']:.3f} (47.8%)")
    
    # 分析匹配结果的合理性
    print(f"\n🔍 匹配结果分析:")
    
    # 1. 页码分析
    print(f"   📖 页码 {match_result['page']} - 合理，在PDF中间部分")
    
    # 2. 区域大小分析
    width = match_result['bbox'][2] - match_result['bbox'][0]
    height = match_result['bbox'][3] - match_result['bbox'][1]
    print(f"   📐 区域大小 {width:.0f}x{height:.0f} - {'大型区域，可能包含完整内容' if height > 400 else '中等区域'}")
    
    # 3. 相似度分析
    similarity = match_result['similarity']
    if similarity >= 0.6:
        similarity_status = "高相似度，匹配良好"
    elif similarity >= 0.4:
        similarity_status = "中等相似度，部分匹配"
    else:
        similarity_status = "低相似度，可能匹配不准确"
    
    print(f"   📊 相似度 {similarity:.3f} - {similarity_status}")
    
    # 4. 内容特征分析
    chunk_keywords = ["元器件", "安装孔", "引线", "直径", "间隙", "印制板", "QJ3012", "GJB4057"]
    print(f"   🔤 关键特征词: {', '.join(chunk_keywords[:5])}")
    
    print(f"\n✅ 验证建议:")
    print(f"   1. 打开PDF第{match_result['page']}页")
    print(f"   2. 查看坐标区域 ({match_result['bbox'][0]:.0f}, {match_result['bbox'][1]:.0f}) 到 ({match_result['bbox'][2]:.0f}, {match_result['bbox'][3]:.0f})")
    print(f"   3. 确认该区域是否包含关键词: {', '.join(chunk_keywords[:3])}")
    print(f"   4. 检查是否有图表 '图1-1' 和标准编号 'QJ3012-98'")
    
    # 简单的提取验证（如果可能）
    try:
        import pymupdf as fitz
        
        pdf_path = "data/航天电子产品常见质量缺陷案例.13610530(2).pdf"
        print(f"\n🔍 尝试提取匹配区域文本...")
        
        doc = fitz.open(pdf_path)
        page = doc[match_result['page'] - 1]  # 转为0索引
        
        # 提取匹配区域文本
        rect = fitz.Rect(match_result['bbox'])
        extracted_text = page.get_textbox(rect)
        
        print(f"📝 提取的文本预览 (前200字符):")
        print("-" * 30)
        print(extracted_text[:200])
        print("-" * 30)
        
        # 简单关键词检查
        found_keywords = []
        for keyword in chunk_keywords:
            if keyword in extracted_text:
                found_keywords.append(keyword)
        
        print(f"✅ 找到的关键词: {found_keywords}")
        print(f"📊 关键词匹配率: {len(found_keywords)}/{len(chunk_keywords)} ({len(found_keywords)/len(chunk_keywords)*100:.1f}%)")
        
        doc.close()
        
        # 最终验证结论
        if len(found_keywords) >= len(chunk_keywords) * 0.5:
            print(f"\n🎉 验证结果: ✅ 匹配有效")
            print(f"   找到了足够的关键词，定位结果可信")
        else:
            print(f"\n⚠️  验证结果: ❓ 匹配可疑")
            print(f"   关键词匹配不足，建议检查")
            
    except Exception as e:
        print(f"\n💡 无法自动提取文本验证: {e}")
        print(f"   请手动打开PDF第{match_result['page']}页验证")

if __name__ == "__main__":
    manual_verify() 