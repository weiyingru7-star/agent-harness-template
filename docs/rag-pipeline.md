# RAG Pipeline

V0.4.0 强化了最小 RAG Pipeline，建立标准化 Document / Chunk / Citation / Retrieval Contract。

## 流程

```
Upload File / Direct Text
  → POST /api/files/upload → POST /api/knowledge/ingest (file_id)
  或
  → POST /api/knowledge/documents (title + text, no upload)
    → Text Extraction
    → Chunking (V0.4.1)
      → char_count / token_count / chunk_metadata
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
| POST | `/api/knowledge/documents` | 直接从文本创建文档 | V0.4.2 |

## Direct Text Ingest

V0.4.2 新增 `POST /api/knowledge/documents`，无需上传文件即可创建文档。

请求字段：
- `title`（必填）：文档标题
- `text`（必填）：文档文本内容
- `collection`（可选，默认 `"default"`）：文档集合
- `source`（可选，默认 `"direct"`）：来源标签
- `content_type`（可选，默认 `"text/plain"`）：内容类型
- `metadata`（可选）：自定义元数据
- `chunking_config`（可选）：切分配置，同 V0.4.1

内部创建虚拟 `FileRecord` 满足外键约束，复用 V0.4.1 chunker 和已有检索链路。
可通过 `POST /api/knowledge/retrieve` 检索到直接创建的文档。

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
