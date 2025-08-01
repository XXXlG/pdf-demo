#!/usr/bin/env python3
"""
RAG知识切片定位FastAPI服务
提供API接口来定位RAG切片在PDF中的坐标位置
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import os
import json
import tempfile
import shutil
from pathlib import Path

from rag_chunk_locator import find_rag_chunk_coordinates, analyze_chunk_content
from mineru_locator import mineru_chunk_locate

# 创建FastAPI应用
app = FastAPI(
    title="RAG切片定位服务",
    description="在PDF文档中精确定位RAG知识切片的坐标位置",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class ChunkLocationRequest(BaseModel):
    """切片定位请求模型"""
    chunk_text: str = Field(..., min_length=5, max_length=10000, description="RAG知识切片内容")
    pdf_path: str = Field(..., description="PDF文件路径")
    similarity_threshold: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="相似度阈值(0-1)")
    
    @validator('chunk_text')
    def validate_chunk_text(cls, v):
        if not v.strip():
            raise ValueError('切片内容不能为空')
        return v.strip()
    
    @validator('pdf_path')
    def validate_pdf_path(cls, v):
        if not v.endswith('.pdf'):
            raise ValueError('必须是PDF文件')
        return v


# 响应模型
class ChunkLocationResponse(BaseModel):
    """切片定位响应模型"""
    success: bool = Field(..., description="是否成功定位")
    page: Optional[int] = Field(None, description="页码")
    bbox: Optional[List[float]] = Field(None, description="坐标边界框 [x0, y0, x1, y1]")
    similarity: Optional[float] = Field(None, description="相似度分数")
    match_type: Optional[str] = Field(None, description="匹配类型")
    found_text_preview: Optional[str] = Field(None, description="找到的文本预览")
    message: str = Field(..., description="响应消息")


class ChunkAnalysisResponse(BaseModel):
    """切片分析响应模型"""
    length: int = Field(..., description="文本长度")
    sentences: int = Field(..., description="句子数量")
    has_numbers: bool = Field(..., description="是否包含数字")
    complexity_score: float = Field(..., description="复杂度评分")


class MineruChunkRequest(BaseModel):
    """MinerU文本定位请求模型"""
    filename: str = Field(..., min_length=1, description="文件名（不含扩展名）")
    text: str = Field(..., min_length=1, max_length=50000, description="待匹配的文本内容")
    similarity_threshold: Optional[float] = Field(0.6, ge=0.0, le=1.0, description="相似度阈值(0-1)")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.strip():
            raise ValueError('文件名不能为空')
        # 移除可能的路径分隔符，确保安全
        v = v.replace('/', '').replace('\\', '').replace('..', '')
        return v.strip()
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('文本内容不能为空')
        return v.strip()


class BlockDetail(BaseModel):
    """文本块详细信息"""
    bbox: List[float] = Field(..., description="文本块边界框")
    bbox_fs: Optional[List[float]] = Field(None, description="更精确的边界框")
    index: int = Field(..., description="文本块索引")


class MineruMatchResult(BaseModel):
    """单个匹配结果"""
    page_idx: int = Field(..., description="页面索引（从0开始）")
    page_size: List[int] = Field(..., description="页面尺寸 [width, height]")
    bbox: List[float] = Field(..., description="合并后的边界框 [x0, y0, x1, y1]")
    similarity: float = Field(..., description="相似度分数")
    block_count: int = Field(..., description="包含的文本块数量")
    matched_text_preview: str = Field(..., description="匹配文本预览")
    block_details: List[BlockDetail] = Field(..., description="各个文本块的详细信息")


class MineruChunkResponse(BaseModel):
    """MinerU文本定位响应模型"""
    success: bool = Field(..., description="是否成功定位")
    message: str = Field(..., description="响应消息")
    query_text: Optional[str] = Field(None, description="查询文本")
    cleaned_text: Optional[str] = Field(None, description="清洗后的文本")
    similarity_threshold: Optional[float] = Field(None, description="使用的相似度阈值")
    results: List[MineruMatchResult] = Field(default=[], description="匹配结果列表")


# API端点
@app.get("/")
async def root():
    """根端点 - 服务状态"""
    return {
        "service": "RAG切片定位服务",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "locate": "/locate - POST - 定位切片位置",
            "analyze": "/analyze - POST - 分析切片内容",
            "upload": "/upload - POST - 上传PDF并定位",
            "mineru-locate": "/mineru-locate - POST - MinerU格式文本定位",
            "health": "/health - GET - 健康检查"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "服务运行正常"}


@app.post("/locate", response_model=ChunkLocationResponse)
async def locate_chunk(request: ChunkLocationRequest):
    """
    定位RAG切片在PDF中的位置
    
    Args:
        request: 包含切片内容和PDF路径的请求
        
    Returns:
        ChunkLocationResponse: 定位结果
    """
    try:
        # 验证PDF文件是否存在
        if not os.path.exists(request.pdf_path):
            raise HTTPException(
                status_code=404, 
                detail=f"PDF文件不存在: {request.pdf_path}"
            )
        
        # 调用核心定位功能，只返回最佳匹配
        results = find_rag_chunk_coordinates(
            chunk_text=request.chunk_text,
            pdf_path=request.pdf_path,
            similarity_threshold=request.similarity_threshold,
            return_best_only=True  # 只返回最佳匹配
        )
        
        if results and len(results) > 0:
            # 获取最佳匹配结果
            best_result = results[0]
            
            # 提取文本预览
            found_text = best_result.get('found_text', '')
            preview = found_text[:200] + "..." if len(found_text) > 200 else found_text
            
            return ChunkLocationResponse(
                success=True,
                page=best_result['page'],
                bbox=best_result['bbox'],
                similarity=round(best_result['similarity'], 3),
                match_type=best_result.get('match_type', 'unknown'),
                found_text_preview=preview,
                message=f"成功定位到第{best_result['page']}页"
            )
        else:
            return ChunkLocationResponse(
                success=False,
                message="未找到匹配的位置，建议降低相似度阈值或检查切片内容"
            )
            
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="PDF文件不存在"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理过程中出现错误: {str(e)}"
        )


@app.post("/analyze", response_model=ChunkAnalysisResponse)
async def analyze_chunk(chunk_text: str = Form(..., description="要分析的切片内容")):
    """
    分析RAG切片内容特征
    
    Args:
        chunk_text: 切片内容
        
    Returns:
        ChunkAnalysisResponse: 分析结果
    """
    try:
        if not chunk_text.strip():
            raise HTTPException(
                status_code=400,
                detail="切片内容不能为空"
            )
        
        # 调用分析功能
        analysis = analyze_chunk_content(chunk_text.strip())
        
        return ChunkAnalysisResponse(
            length=analysis['length'],
            sentences=analysis['sentences'],
            has_numbers=analysis['has_numbers'],
            complexity_score=round(analysis['complexity_score'], 3)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分析过程中出现错误: {str(e)}"
        )


@app.post("/upload", response_model=ChunkLocationResponse)
async def upload_and_locate(
    chunk_text: str = Form(..., description="RAG知识切片内容"),
    similarity_threshold: float = Form(0.5, description="相似度阈值"),
    pdf_file: UploadFile = File(..., description="PDF文件")
):
    """
    上传PDF文件并定位切片位置
    
    Args:
        chunk_text: 切片内容
        similarity_threshold: 相似度阈值
        pdf_file: 上传的PDF文件
        
    Returns:
        ChunkLocationResponse: 定位结果
    """
    try:
        # 验证文件类型
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="只支持PDF文件"
            )
        
        # 验证切片内容
        if not chunk_text.strip():
            raise HTTPException(
                status_code=400,
                detail="切片内容不能为空"
            )
        
        # 验证相似度阈值
        if not 0 <= similarity_threshold <= 1:
            raise HTTPException(
                status_code=400,
                detail="相似度阈值必须在0-1之间"
            )
        
        # 创建临时文件保存上传的PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(pdf_file.file, temp_file)
            temp_pdf_path = temp_file.name
        
        try:
            # 调用定位功能
            results = find_rag_chunk_coordinates(
                chunk_text=chunk_text.strip(),
                pdf_path=temp_pdf_path,
                similarity_threshold=similarity_threshold,
                return_best_only=True
            )
            
            if results and len(results) > 0:
                best_result = results[0]
                
                # 提取文本预览
                found_text = best_result.get('found_text', '')
                preview = found_text[:200] + "..." if len(found_text) > 200 else found_text
                
                return ChunkLocationResponse(
                    success=True,
                    page=best_result['page'],
                    bbox=best_result['bbox'],
                    similarity=round(best_result['similarity'], 3),
                    match_type=best_result.get('match_type', 'unknown'),
                    found_text_preview=preview,
                    message=f"成功定位到第{best_result['page']}页"
                )
            else:
                return ChunkLocationResponse(
                    success=False,
                    message="未找到匹配的位置，建议降低相似度阈值或检查切片内容"
                )
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理过程中出现错误: {str(e)}"
        )


@app.post("/mineru-locate", response_model=MineruChunkResponse)
async def mineru_locate_chunk(request: MineruChunkRequest):
    """
    MinerU格式文本定位接口
    根据文本匹配其在全文中的坐标和页码索引
    
    Args:
        request: 包含文件名和文本内容的请求
        
    Returns:
        MineruChunkResponse: 定位结果
    """
    try:
        # 调用核心定位功能
        result = mineru_chunk_locate(
            filename=request.filename,
            text=request.text,
            similarity_threshold=request.similarity_threshold
        )
        
        # 转换结果格式
        if result['success']:
            # 转换匹配结果
            match_results = []
            for match in result['results']:
                block_details = []
                for detail in match['block_details']:
                    block_details.append(BlockDetail(
                        bbox=detail['bbox'],
                        bbox_fs=detail.get('bbox_fs'),
                        index=detail['index']
                    ))
                
                match_results.append(MineruMatchResult(
                    page_idx=match['page_idx'],
                    page_size=match['page_size'],
                    bbox=match['bbox'],
                    similarity=match['similarity'],
                    block_count=match['block_count'],
                    matched_text_preview=match['matched_text_preview'],
                    block_details=block_details
                ))
            
            return MineruChunkResponse(
                success=True,
                message=result['message'],
                query_text=result.get('query_text'),
                cleaned_text=result.get('cleaned_text'),
                similarity_threshold=result.get('similarity_threshold'),
                results=match_results
            )
        else:
            return MineruChunkResponse(
                success=False,
                message=result['message'],
                query_text=result.get('query_text'),
                cleaned_text=result.get('cleaned_text'),
                similarity_threshold=result.get('similarity_threshold'),
                results=[]
            )
            
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="指定的middle.json文件不存在"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"请求参数错误: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理过程中出现错误: {str(e)}"
        )


@app.get("/docs-info")
async def get_api_docs():
    """获取API文档信息"""
    return {
        "message": "API文档",
        "interactive_docs": "/docs",
        "openapi_schema": "/openapi.json",
        "examples": {
            "locate_example": {
                "chunk_text": "元器件安装孔与元器件引线不匹配",
                "pdf_path": "data/航天电子产品常见质量缺陷案例.13610530(2).pdf",
                "similarity_threshold": 0.5
            },
            "mineru_locate_example": {
                "filename": "航天电子产品常见质量缺陷案例.13610530(2)",
                "text": "元器件安装孔与元器件引线不匹配",
                "similarity_threshold": 0.6
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # 启动开发服务器
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    ) 