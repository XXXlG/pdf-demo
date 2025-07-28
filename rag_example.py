#!/usr/bin/env python3
"""
RAG知识切片坐标定位使用示例 - 优化版
演示如何精确定位单个知识切片在PDF中的位置
"""

from rag_chunk_locator import find_rag_chunk_coordinates, analyze_chunk_content

def simple_example():
    """简单使用示例 - 返回最佳匹配"""
    
    # 模拟RAG系统中的知识切片
    knowledge_chunk = r"""
6）大面积覆铜区域的元器件安装孔设计缺陷# 问题描述大面积覆铜区域上的焊盘设计没有做出隔离蚀刻区域进行热隔离，会导致散热过快，容易形成透锡不良的焊点，见图1-8所示。  ![](http://192.168.0.130:94/images/cf8ddd7b7217ef5ef02edb7843a682e6a1d58e6d735607e9968bd37c7d53f24f.jpg)  缺陷案例照片、图片  图1-8大面积覆铜区域上的焊盘设计缺陷缺陷案例照片、图片![](http://192.168.0.130:94/images/cf8ddd7b7217ef5ef02edb7843a682e6a1d58e6d735607e9968bd37c7d53f24f.jpg)![](http://192.168.0.130:94/images/fd2e47626fa542aa7ea38cb59a973e31e8771007654d1169d1bcf48b97e4ab2a.jpg)![](http://192.168.0.130:94/images/79a775c251e1c684eca88831d5e12bf777e51b53e0404003ec88c1124553c1ef.jpg)# 正确方法需要焊接的部分尽量避免布设超过 $6 ~ \mathrm { c m } ^ { 2 }$ 的导电面积，如果大的导电面积上有焊点，其焊接部位应在保持其导体连续性的基础上，做出隔离蚀刻区域以进行热隔离。焊接可操作性的排列顺序一般为：焊盘通过隔热导线连接到地层、花焊盘与网格状地相连、花焊盘与实芯地层相连、焊盘直接与实芯地层相连。# 依据文件、标准或规范QJ3013A-2011第5.6.2.3节规定：对印制板表面较大的导电面积（大于 $2 5 ~ \mathrm { m m } \times 2 5 ~ \mathrm { m m }$ ）应采用网格式的窗口，以减少焊接过程中对热量的吸收；如果有焊盘，应进行热隔离，并保持电气连接，可以避免大的导电面积在焊接时因热量积累而起泡；多层印制板内层地、电层铜箔面上如果有连接盘，也应进行热隔离；在焊接时减少散热速度，使热量集中在焊盘上，以有利于焊接。但作为微带线和带状线的镜像接地面，不能开网格式的窗口，以免引起导线特性阻抗的变化。热隔离焊盘见图1-9所示。  ![](http://192.168.0.130:94/images/fd2e47626fa542aa7ea38cb59a973e31e8771007654d1169d1bcf48b97e4ab2a.jpg)  图1-9大导电面积的散热窗口和隔热焊盘设计  GJB4057-2000第6.4.3节规定：对于大于 $5 \times 5 ~ \mathrm { m m } ^ { 2 }$ 的大面积导电图形，应局部开窗口；电源层、地层大面积图形与其连接盘之间应进行热隔离设计，如图1-10所示。  ![](http://192.168.0.130:94/images/79a775c251e1c684eca88831d5e12bf777e51b53e0404003ec88c1124553c1ef.jpg)  图1-10电源层、地层热隔离
    """
    
    # PDF文件路径
    pdf_file = "data/航天电子产品常见质量缺陷案例.13610530(2).pdf"
    
    print("RAG知识切片精确定位示例")
    print("=" * 50)
    
    # 1. 分析切片内容
    print("1. 分析知识切片...")
    analysis = analyze_chunk_content(knowledge_chunk)
    
    print(f"切片长度: {analysis['length']} 字符")
    print(f"句子数量: {analysis['sentences']}")
    print(f"包含数字: {analysis['has_numbers']}")
    print(f"复杂度评分: {analysis['complexity_score']:.2f}")
    
    # 2. 定位切片在PDF中的位置（只返回最佳匹配）
    print("\n2. 定位切片最佳位置...")
    try:
        results = find_rag_chunk_coordinates(
            knowledge_chunk, 
            pdf_file,
            similarity_threshold=0.3,  # 可以调整相似度阈值
            return_best_only=True     # 只返回最佳匹配
        )
        
        if results:
            result = results[0]  # 只有一个最佳结果
            print("✅ 找到最佳匹配位置:")
            print(f"   📄 页码: {result['page']}")
            print(f"   📍 坐标: {result['bbox']}")  # [x0, y0, x1, y1]
            print(f"   🎯 匹配类型: {result['match_type']}")
            print(f"   📊 相似度: {result['similarity']:.3f}")
            
            # 显示匹配的文本预览
            if 'found_text' in result:
                preview = result['found_text'][:200] + "..." if len(result['found_text']) > 200 else result['found_text']
                print(f"   📝 匹配文本预览: {preview}")
            
            print(f"\n🎉 切片已成功定位到第 {result['page']} 页的坐标 {result['bbox']}")
            
        else:
            print("❌ 未找到匹配位置")
            print("💡 建议: 尝试降低相似度阈值或检查切片内容")
        
    except FileNotFoundError:
        print(f"❌ 找不到PDF文件: {pdf_file}")
        print("💡 请确保文件路径正确")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")


def advanced_example():
    """高级示例 - 展示多种匹配选项"""
    
    # 较短的知识切片
    short_chunk = "元器件安装孔与元器件引线不匹配，导致元器件引线无法安装或间隙过小，容易导致安装孔损伤。"
    
    pdf_file = "data/航天电子产品常见质量缺陷案例.13610530(2).pdf"
    
    print("\n高级匹配示例")
    print("=" * 30)
    
    # 比较不同阈值的效果
    thresholds = [0.3, 0.5, 0.7]
    
    for threshold in thresholds:
        print(f"\n📊 相似度阈值: {threshold}")
        
        try:
            # 返回所有候选匹配
            results = find_rag_chunk_coordinates(
                short_chunk, 
                pdf_file,
                similarity_threshold=threshold,
                return_best_only=False  # 返回所有匹配
            )
            
            print(f"   找到 {len(results)} 个匹配区域")
            
            for i, result in enumerate(results[:3], 1):  # 只显示前3个
                print(f"   {i}. 页{result['page']} | 相似度: {result['similarity']:.3f} | 类型: {result.get('match_type', 'N/A')}")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")


def test_with_custom_chunk():
    """测试自定义切片"""
    
    # 用户可以替换这里的内容
    custom_chunk = input("\n请输入要定位的知识切片内容 (或直接回车使用默认): ").strip()
    
    if not custom_chunk:
        custom_chunk = "印制板元器件安装孔成孔公称直径与元器件引线公称直径之间应有合理间隙"
    
    pdf_file = "data/航天电子产品常见质量缺陷案例.13610530(2).pdf"
    
    print(f"\n🔍 正在定位: {custom_chunk[:50]}...")
    
    try:
        results = find_rag_chunk_coordinates(
            custom_chunk, 
            pdf_file,
            similarity_threshold=0.4,  # 稍微宽松的阈值
            return_best_only=True
        )
        
        if results:
            result = results[0]
            print(f"✅ 定位成功!")
            print(f"   页码: {result['page']}")
            print(f"   坐标: {result['bbox']}")
            print(f"   相似度: {result['similarity']:.3f}")
        else:
            print("❌ 未找到匹配位置")
            
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    # 运行基本示例
    simple_example()
    
    # 运行高级示例
    advanced_example()
    
    # 交互式测试
    test_with_custom_chunk() 