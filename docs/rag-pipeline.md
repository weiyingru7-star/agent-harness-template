# RAG Pipeline

V0.4.0 强化了最小 RAG Pipeline，建立标准化 Document / Chunk / Citation / Retrieval Contract。

## 流程

```
Upload File
  → POST /api/files/upload
  → POST /api/knowledge/ingest (file_id)
    → Text Extraction (已存在)
    → Simple Chunking (V0.4.0 enchancment)
      → char_count / token_count 计算
    → Document + Chunks 写入数据库
  → 检索: POST /api/knowledge/retrieve (query)
    → Keyword matching (无 embedding)
    → Score calculation (term frequency)
    → Citation builder (含 quote / score / title / source)
```

## API 路由

| 方法 | 路径 | 用途 | 版本 |
|---|---|---|---|
| POST | `/api/knowledge/ingest` | 上传文件后 ingest 为文档 | V0 |
| GET | `/api/knowledge/documents` | 列出所有文档 | V0 |
| POST | `/api/knowledge/retrieve` | 检索文档 | V0 |
| GET | `/api/knowledge/documents/{document_id}` | 查询单文档详情 | V0.4.0 |
| GET | `/api/knowledge/collections/{collection}/chunks` | 按集合查询分块 | V0.4.0 |

## 分块

`harness/rag/chunking.py` 的 `chunk_text` 按段落（`\n\n`）分块，默认每块最多 500 字符。
V0.4.0 在 ingest 时计算 `char_count` 和 `token_count`（space-split 近似）。

## 检索

`harness/rag/store.py` 的 `retrieve` 使用关键词计数算法（不接 embedding 或向量库）。
每个 chunk 按查询词出现次数计分，返回按分数降序排列的结果。

## Citation

每个检索结果包含 Citation，含：
- 源文档标识（document_id、file_id、filename）
- 匹配文本片段（quote，前 200 字符）
- 匹配分数（score）
- 文档元信息级联（title、source、collection）

## 未来能力

- V0.4.x：embedding provider、向量库集成
- V0.4.x：Rerank
- V0.4.x：RAG Eval
- V0.4.x：复杂文档解析（PDF、Word、Excel）
- V0.4.x：实时索引更新
