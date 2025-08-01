# MinerU文本定位接口使用说明

## 接口概述

`mineru_chunk_locate()` 接口用于根据文本内容在MinerU格式的JSON文件中匹配对应的坐标和页码索引。

## 接口地址

```
POST /mineru-locate
```

## 功能特点

1. **文本清洗**: 自动去除特殊符号和多余空格
2. **智能匹配**: 支持连续文本块的组合匹配
3. **相似度计算**: 基于序列相似度算法
4. **多结果返回**: 支持返回多个匹配区域
5. **坐标合并**: 自动计算多个文本块的合并边界框

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 文件名（不含扩展名），系统会自动在data目录下查找对应的_middle.json文件 |
| text | string | 是 | 待匹配的文本内容，长度1-50000字符 |
| similarity_threshold | float | 否 | 相似度阈值(0-1)，默认0.6 |

## 响应格式

```json
{
  "success": true,
  "message": "找到 2 个匹配区域",
  "query_text": "航天科技图书出版基金资助出版",
  "cleaned_text": "航天科技图书出版基金资助出版",
  "similarity_threshold": 0.6,
  "results": [
    {
      "page_idx": 0,
      "page_size": [410, 583],
      "bbox": [122, 46, 315, 65],
      "similarity": 0.985,
      "block_count": 1,
      "matched_text_preview": "航天科技图书出版基金资助出版",
      "block_details": [
        {
          "bbox": [122, 46, 315, 65],
          "bbox_fs": [122, 46, 315, 65],
          "index": 0
        }
      ]
    }
  ]
}
```

## 响应字段说明

### 主要字段
- `success`: 是否成功定位
- `message`: 响应消息
- `query_text`: 原始查询文本
- `cleaned_text`: 清洗后的文本
- `similarity_threshold`: 使用的相似度阈值
- `results`: 匹配结果数组

### 匹配结果字段
- `page_idx`: 页面索引（从0开始）
- `page_size`: 页面尺寸 [width, height]
- `bbox`: 合并后的边界框 [x0, y0, x1, y1]
- `similarity`: 相似度分数
- `block_count`: 包含的文本块数量
- `matched_text_preview`: 匹配文本预览
- `block_details`: 各个文本块的详细信息

## 使用示例

### Python 示例

```python
import requests

# 请求数据
data = {
    "filename": "航天电子产品常见质量缺陷案例.13610530(2)",
    "text": "航天科技图书出版基金资助出版",
    "similarity_threshold": 0.6
}

# 发送请求
response = requests.post("http://localhost:8004/mineru-locate", json=data)

if response.status_code == 200:
    result = response.json()
    if result['success']:
        print(f"找到 {len(result['results'])} 个匹配区域")
        for i, match in enumerate(result['results']):
            print(f"第 {i+1} 个匹配:")
            print(f"  页面: {match['page_idx']}")
            print(f"  相似度: {match['similarity']}")
            print(f"  坐标: {match['bbox']}")
    else:
        print(f"匹配失败: {result['message']}")
else:
    print(f"请求失败: {response.status_code}")
```

### cURL 示例

```bash
curl -X POST "http://localhost:8004/mineru-locate" \
     -H "Content-Type: application/json" \
     -d '{
       "filename": "航天电子产品常见质量缺陷案例.13610530(2)",
       "text": "航天科技图书出版基金资助出版",
       "similarity_threshold": 0.6
     }'
```

### JavaScript 示例

```javascript
const data = {
    filename: "航天电子产品常见质量缺陷案例.13610530(2)",
    text: "航天科技图书出版基金资助出版",
    similarity_threshold: 0.6
};

fetch("http://localhost:8004/mineru-locate", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
    if (result.success) {
        console.log(`找到 ${result.results.length} 个匹配区域`);
        result.results.forEach((match, index) => {
            console.log(`第 ${index + 1} 个匹配:`);
            console.log(`  页面: ${match.page_idx}`);
            console.log(`  相似度: ${match.similarity}`);
            console.log(`  坐标: [${match.bbox.join(', ')}]`);
        });
    } else {
        console.log(`匹配失败: ${result.message}`);
    }
})
.catch(error => console.error("请求错误:", error));
```

## 错误处理

### 常见错误代码

- `400`: 请求参数错误（文本为空、文件名无效等）
- `404`: 指定的middle.json文件不存在
- `500`: 服务器内部错误

### 错误响应示例

```json
{
  "detail": "指定的middle.json文件不存在"
}
```

## 性能优化建议

1. **文本长度**: 建议文本长度在100-5000字符之间，过短可能匹配不准确，过长可能影响性能
2. **相似度阈值**: 
   - 精确匹配：使用0.8-1.0
   - 模糊匹配：使用0.5-0.7
   - 宽松匹配：使用0.3-0.5
3. **文件缓存**: 系统会自动缓存JSON文件，重复查询同一文件性能更好

## 算法说明

### 文本清洗
- 移除多余空白字符和换行符
- 保留中英文、数字和基本标点符号
- 统一空格处理

### 匹配策略
1. 从每个文本块开始，尝试向后连续匹配
2. 计算组合文本的相似度
3. 当相似度低于阈值时停止扩展
4. 返回所有超过阈值的匹配区域

### 坐标计算
- 合并多个文本块的边界框
- 计算最小外接矩形
- 支持精确坐标(bbox_fs)和普通坐标(bbox)

## 交互式文档

启动API服务后，可以访问以下地址查看交互式API文档：

- Swagger UI: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc
- OpenAPI Schema: http://localhost:8004/openapi.json