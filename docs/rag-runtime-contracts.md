# RAG Runtime Contracts 数据合同

V0.4.0–V0.4.6 定义了 6 个主要数据合同。

## 合同一览

| 合同 | 版本 | Schema 位置 | 主要字段 |
|---|---|---|---|
| Document | V0.4.0 | `schemas/document.schema.json` | id, file_id, filename, collection, title, source, content_type, created_at |
| Chunk | V0.4.0–0.4.1 | `schemas/chunk.schema.json` | id, document_id, text, index, collection, char_count, token_count, chunk_metadata |
| Citation | V0.4.0 | `schemas/citation.schema.json` | document_id, chunk_id, file_id, filename, chunk_index, title, source, quote, score, collection |
| RetrievalResult | V0.4.0–0.4.6 | `schemas/retrieval-result.schema.json` | chunk, score, citation, retrieval_mode, score_type |
| Embedding | V0.4.4 | `schemas/embedding.schema.json` | EmbeddingRequest(input, model), EmbeddingResult(embeddings, dimensions) |
| VectorStore | V0.4.5 | `schemas/vector-store.schema.json` | VectorRecord(vector, document_id), VectorSearchRequest(query_vector, collection, top_k), VectorSearchResult(score) |

## Retrieval Mode 合同

### 请求

`POST /api/knowledge/retrieve` 新增字段：

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `retrieval_mode` | string | `"keyword"` | `"keyword"` / `"vector"` / `"hybrid"` |
| `collection` | string \| null | null | vector 模式集合过滤 |

### 三种模式

| 模式 | 算法 | score_type | 依赖 | 默认 |
|---|---|---|---|---|
| `keyword` | term frequency | `term_frequency` | 无 | 默认 |
| `vector` | cosine similarity (dot product) | `cosine` | MockEmbeddingProvider + InMemoryVectorStore | 可选 |
| `hybrid` | keyword + vector dedup merge | `cosine` | 同上 + keyword | 可选 |

### 响应 metadata

```json
{
  "metadata": {
    "retrieval_mode": "keyword",
    "score_type": "term_frequency",
    "retriever": "KnowledgeStore.keyword"
  }
}
```

vector / hybrid 模式额外包含 `embedding_provider: "mock-embedding"` 和 `vector_store: "InMemoryVectorStore"`。

每个 `results[i]` 也包含 `retrieval_mode` / `score_type` 字段。

## 文件位置

- 模型定义：`harness/rag/models.py`
- Schema 契约：`schemas/*.schema.json`
- 存储操作：`harness/rag/store.py`
- 嵌入层：`harness/rag/embeddings.py`
- 向量存储：`harness/rag/vector_store.py`
