#!/usr/bin/env python3
"""
RAG切片定位API客户端使用示例
演示如何调用FastAPI服务进行切片定位
"""

import requests
import json
from typing import Dict, Any

class RAGChunkLocatorClient:
    """RAG切片定位API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url.rstrip('/')
        
    def check_health(self) -> Dict[str, Any]:
        """检查服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def locate_chunk(self, chunk_text: str, pdf_path: str, 
                    similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        定位切片在PDF中的位置
        
        Args:
            chunk_text: 切片内容
            pdf_path: PDF文件路径
            similarity_threshold: 相似度阈值
            
        Returns:
            定位结果
        """
        data = {
            "chunk_text": chunk_text,
            "pdf_path": pdf_path,
            "similarity_threshold": similarity_threshold
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/locate",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "message": f"请求失败: {e}"}
    
    def analyze_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """
        分析切片内容
        
        Args:
            chunk_text: 切片内容
            
        Returns:
            分析结果
        """
        data = {"chunk_text": chunk_text}
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                data=data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"请求失败: {e}"}
    
    def upload_and_locate(self, chunk_text: str, pdf_file_path: str,
                         similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        上传PDF文件并定位切片
        
        Args:
            chunk_text: 切片内容
            pdf_file_path: 本地PDF文件路径
            similarity_threshold: 相似度阈值
            
        Returns:
            定位结果
        """
        try:
            with open(pdf_file_path, 'rb') as pdf_file:
                files = {'pdf_file': pdf_file}
                data = {
                    'chunk_text': chunk_text,
                    'similarity_threshold': similarity_threshold
                }
                
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
        except FileNotFoundError:
            return {"success": False, "message": f"文件不存在: {pdf_file_path}"}
        except requests.RequestException as e:
            return {"success": False, "message": f"请求失败: {e}"}


def main():
    """示例用法"""
    # 创建客户端
    client = RAGChunkLocatorClient()
    
    print("🔍 RAG切片定位API客户端示例")
    print("=" * 50)
    
    # 1. 检查服务状态
    print("1. 检查服务状态...")
    health = client.check_health()
    print(f"   状态: {health}")
    
    if health.get("status") != "healthy":
        print("❌ 服务未运行，请先启动API服务")
        print("💡 运行: python start_api.py")
        return
    
    # 2. 分析切片内容
    print("\n2. 分析切片内容...")
    test_chunk = "元器件安装孔与元器件引线不匹配，导致元器件引线无法安装或间隙过小"
    
    analysis = client.analyze_chunk(test_chunk)
    print(f"   切片长度: {analysis.get('length')} 字符")
    print(f"   句子数量: {analysis.get('sentences')}")
    print(f"   复杂度评分: {analysis.get('complexity_score')}")
    
    # 3. 定位切片（使用服务器上的PDF文件）
    print("\n3. 定位切片位置...")
    pdf_path = "data/航天电子产品常见质量缺陷案例.13610530(2).pdf"
    
    result = client.locate_chunk(
        chunk_text=test_chunk,
        pdf_path=pdf_path,
        similarity_threshold=0.4
    )
    
    if result.get("success"):
        print("✅ 定位成功!")
        print(f"   📄 页码: {result['page']}")
        print(f"   📍 坐标: {result['bbox']}")
        print(f"   🎯 相似度: {result['similarity']}")
        print(f"   📝 匹配类型: {result['match_type']}")
        print(f"   📖 文本预览: {result['found_text_preview'][:100]}...")
    else:
        print("❌ 定位失败")
        print(f"   原因: {result['message']}")
    
    # 4. 演示文件上传定位（如果有本地PDF文件）
    print("\n4. 文件上传定位示例...")
    if input("是否测试文件上传功能? (y/n): ").lower() == 'y':
        local_pdf = input("请输入本地PDF文件路径: ")
        if local_pdf and local_pdf.endswith('.pdf'):
            upload_result = client.upload_and_locate(
                chunk_text=test_chunk,
                pdf_file_path=local_pdf,
                similarity_threshold=0.4
            )
            
            if upload_result.get("success"):
                print("✅ 上传并定位成功!")
                print(f"   📄 页码: {upload_result['page']}")
                print(f"   📍 坐标: {upload_result['bbox']}")
                print(f"   🎯 相似度: {upload_result['similarity']}")
            else:
                print("❌ 上传定位失败")
                print(f"   原因: {upload_result['message']}")
        else:
            print("⏭️  跳过文件上传测试")
    
    print("\n🎉 示例完成!")
    print("💡 更多API信息请访问: http://localhost:80004/docs")


def interactive_test():
    """交互式测试"""
    client = RAGChunkLocatorClient()
    
    print("🔍 交互式RAG切片定位测试")
    print("=" * 40)
    
    # 检查服务
    health = client.check_health()
    if health.get("status") != "healthy":
        print("❌ 服务未运行，请先启动API服务")
        return
    
    while True:
        print("\n请选择操作:")
        print("1. 定位切片")
        print("2. 分析切片")
        print("3. 退出")
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == '1':
            chunk_text = input("请输入切片内容: ").strip()
            pdf_path = input("请输入PDF路径: ").strip()
            
            try:
                threshold = float(input("请输入相似度阈值 (0-1, 默认0.5): ") or "0.5")
            except ValueError:
                threshold = 0.5
            
            if chunk_text and pdf_path:
                result = client.locate_chunk(chunk_text, pdf_path, threshold)
                print(f"\n结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print("❌ 请输入有效的切片内容和PDF路径")
                
        elif choice == '2':
            chunk_text = input("请输入要分析的切片内容: ").strip()
            if chunk_text:
                result = client.analyze_chunk(chunk_text)
                print(f"\n分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print("❌ 请输入有效的切片内容")
                
        elif choice == '3':
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        main() 