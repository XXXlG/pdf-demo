#!/usr/bin/env python3
"""
RAG切片定位API服务启动脚本
"""

import uvicorn
import sys
import os

def main():
    """启动API服务"""
    print("🚀 启动RAG切片定位API服务...")
    print("📍 服务地址: http://localhost:8004")
    print("📖 API文档: http://localhost:8004/docs")
    print("🏥 健康检查: http://localhost:8004/health")
    print("-" * 50)
    
    try:
        # 启动服务
        uvicorn.run(
            "api_service:app",
            host="0.0.0.0",
            port=8004,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 