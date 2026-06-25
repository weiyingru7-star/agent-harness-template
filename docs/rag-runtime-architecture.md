# RAG Runtime Architecture 运行架构

V0.4.0–V0.4.6 构建了一个完整的 RAG Pipeline。本文档用文本架构图说明整体数据流。

## Pipeline 架构

```
             ┌──────────────────────┐
             │   Text / File Input  │
             │  (Direct text or     │
             │   file upload)       │
             └──────┬───────────────┘
                    │
                    ↓
        ┌───────────────────────────┐
        │  Document Normalizer      │
        │  + Chunking Strategy      │  V0.4.0–V0.4.1
        │  paragraph-first / fixed  │
        │  char_count / token_count │
        │  chunk_metadata (offset,  │
        │   split_strategy, overlap)│
        └──────┬────────────────────┘
               │
        ┌──────▼────────────────────┐
        │  Embedding (optional)     │  V0.4.4
        │  MockEmbeddingProvider    │
        │  8-dim deterministic      │
        │  L2-normalized vectors    │
        └──────┬────────────────────┘
               │
        ┌──────▼────────────────────┐
        │  Vector Store (optional)  │  V0.4.5
        │  InMemoryVectorStore      │
        │  dict-backed, lazy index  │
        │  cosine similarity (dot)  │
        └──────┬────────────────────┘
               │
        ┌──────▼────────────────────┐
        │  Retrieve API             │  V0.4.6
        │  ┌─ keyword (term freq)  │  (default)
        │  ├─ vector (cosine)      │
        │  └─ hybrid (dedup)       │
        └──────┬────────────────────┘
               │
        ┌──────▼────────────────────┐
        │  RetrievalResult          │  V0.4.0
        │  + Citation               │
        │  + retrieval_mode         │
        │  + score_type             │
        └──────┬────────────────────┘
               │
        ┌──────▼────────────────────┐
        │  RAG Eval                 │  V0.4.3
        │  scripts/run_rag_evals.py │
        │  structured test cases    │
        └───────────────────────────┘
```

## 数据流（按版本顺序）

```
POST /api/knowledge/documents (title + text)
  → Document(id, file_id, collection, title, source, content_type)     V0.4.0
  → Chunk(id, document_id, text, index, char_count, token_count,
           chunk_metadata)                                             V0.4.0–0.4.1
  → (可选) MockEmbeddingProvider.embed(chunk.text) → 8-dim vector       V0.4.4
  → (可选) InMemoryVectorStore.upsert(VectorRecord)                     V0.4.5
  → POST /api/knowledge/retrieve(query, retrieval_mode)                V0.4.6
    → keyword: term frequency scoring
    → vector: cosine similarity search
    → hybrid: keyword + vector dedup merge
  → RetrieveResult(chunk, score, citation, retrieval_mode, score_type)
  → RetrieveResponse(query, results, metadata)
```

## 关键设计决策

- keyword 是默认模式，零依赖，与 V0.4.0 行为一致
- vector 模式惰性建索引（首次请求时从 DB chunks 构建），不修改 ingest
- hybrid 模式简单去重合并，不做复杂权重融合
- 不接真实 embedding API / 向量数据库
- 不暴露 embedding HTTP API（遵循 V0.4.4 先例）

## 相关文档

- [RAG Runtime 总入口](rag-runtime.md)
- [RAG Runtime Contracts](rag-runtime-contracts.md)
- [RAG Runtime Eval](rag-runtime-eval.md)
