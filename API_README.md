# RAG切片定位API服务

这是一个基于FastAPI的RAG知识切片定位服务，可以精确定位RAG切片在PDF文档中的坐标位置。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python start_api.py
```

服务将在 `http://localhost:8004` 启动

### 3. 访问API文档

打开浏览器访问：
- 交互式API文档：http://localhost:80004/docs
- 服务状态：http://localhost:80004/health

## 📖 API接口

### 1. `/locate` - 定位切片位置

**POST** `/locate`

定位RAG切片在指定PDF文件中的最佳匹配位置。

**请求体：**
```json
{
  "chunk_text": "元器件安装孔与元器件引线不匹配",
  "pdf_path": "data/航天电子产品常见质量缺陷案例.13610530(2).pdf",
  "similarity_threshold": 0.5
}
```

**响应：**
```json
{
  "success": true,
  "page": 15,
  "bbox": [100.5, 200.2, 450.8, 280.1],
  "similarity": 0.87,
  "match_type": "直接文本匹配",
  "found_text_preview": "元器件安装孔与元器件引线不匹配，导致...",
  "message": "成功定位到第15页"
}
```

### 2. `/upload` - 上传PDF并定位

**POST** `/upload`

上传PDF文件并定位切片位置。

**参数：**
- `chunk_text` (form): 切片内容
- `similarity_threshold` (form): 相似度阈值
- `pdf_file` (file): PDF文件

### 3. `/analyze` - 分析切片内容

**POST** `/analyze`

分析切片内容的特征。

**参数：**
- `chunk_text` (form): 要分析的切片内容

**响应：**
```json
{
  "length": 45,
  "sentences": 2,
  "has_numbers": false,
  "complexity_score": 0.35
}
```

### 4. `/health` - 健康检查

**GET** `/health`

检查服务运行状态。

## 🛠️ 使用示例

### Python客户端

```python
import requests

# 定位切片
response = requests.post("http://localhost:80004/locate", json={
    "chunk_text": "你的切片内容",
    "pdf_path": "你的PDF文件路径",
    "similarity_threshold": 0.5
})

result = response.json()
if result["success"]:
    print(f"找到匹配位置：第{result['page']}页")
    print(f"坐标：{result['bbox']}")
    print(f"相似度：{result['similarity']}")
```

### 使用客户端示例

运行完整的客户端示例：

```bash
python api_client_example.py
```

交互式测试：

```bash
python api_client_example.py interactive
```

### curl 示例

```bash
# 定位切片
curl -X POST "http://localhost:80004/locate" \
     -H "Content-Type: application/json" \
     -d '{
       "chunk_text": "元器件安装孔与元器件引线不匹配",
       "pdf_path": "data/航天电子产品常见质量缺陷案例.13610530(2).pdf",
       "similarity_threshold": 0.5
     }'

# 健康检查
curl http://localhost:80004/health
```

## 📋 响应字段说明

### 定位响应字段

- `success`: 是否成功定位
- `page`: 页码（从1开始）
- `bbox`: 坐标边界框 `[x0, y0, x1, y1]`
  - `x0, y0`: 左上角坐标
  - `x1, y1`: 右下角坐标
- `similarity`: 相似度分数 (0-1)
- `match_type`: 匹配类型
  - `"直接文本匹配"`: 找到完全匹配的文本
  - `"关键词匹配"`: 基于关键词的匹配
  - `"模糊匹配"`: 相似度匹配
- `found_text_preview`: 找到的文本预览
- `message`: 响应消息

## ⚙️ 配置说明

### 相似度阈值

- 范围：0.0 - 1.0
- 默认：0.5
- 建议：
  - `0.7-1.0`: 严格匹配，要求高相似度
  - `0.5-0.7`: 平衡匹配，推荐使用
  - `0.3-0.5`: 宽松匹配，可能包含更多候选

### 匹配策略

系统根据切片长度自动选择匹配策略：
- **短文本** (< 100字符): 使用多种匹配方法，包容性更强
- **长文本** (≥ 100字符): 使用整体匹配，精确度更高

## 🔧 开发和调试

### 启用调试模式

修改 `start_api.py` 中的 `reload=True` 可以启用热重载模式。

### 查看日志

服务运行时会输出详细的处理日志，包括：
- 匹配策略选择
- 关键词提取
- 相似度计算过程

### 错误处理

API返回标准的HTTP状态码：
- `200`: 成功
- `400`: 请求参数错误
- `404`: 文件不存在
- `500`: 服务器内部错误

## 🎯 最佳实践

1. **PDF路径**: 使用绝对路径或相对于服务启动目录的路径
2. **切片长度**: 建议50-500字符，过短或过长都可能影响匹配效果
3. **相似度阈值**: 从0.5开始测试，根据效果调整
4. **文件上传**: 大文件建议使用 `/locate` 接口而非 `/upload`

## 📁 项目结构

```
pdf-demo/
├── api_service.py          # FastAPI服务主文件
├── start_api.py           # 服务启动脚本
├── api_client_example.py  # 客户端示例
├── rag_chunk_locator.py   # 核心定位功能
├── requirements.txt       # 依赖包
└── data/                  # PDF文件目录
```

## 🐛 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口80004是否被占用
   - 确认所有依赖已正确安装

2. **PDF文件不存在错误**
   - 检查文件路径是否正确
   - 确认PDF文件可读

3. **定位失败**
   - 尝试降低相似度阈值
   - 检查切片内容是否确实在PDF中
   - 确认PDF文本可以正常提取

### 获取帮助

- 查看API文档：http://localhost:80004/docs
- 运行健康检查：http://localhost:80004/health
- 使用客户端示例进行测试 