# RAG Runtime 工具执行运行时

V0.4.0–V0.4.6 构建了一个完整的 RAG Runtime 栈。本文档是整个 RAG Runtime 文档体系的总入口。

## 模块总览

| 模块 | 版本 | 说明 | 文档 |
|---|---|---|---|
| 数据合同 | V0.4.0 | Document / Chunk / Citation / RetrievalResult | [RAG Contracts](rag-contracts.md) |
| 切分策略 | V0.4.1 | chunk_size / chunk_overlap / paragraph split / metadata | [RAG Chunking](rag-chunking.md) |
| 直接文本创建 | V0.4.2 | POST /api/knowledge/documents | [RAG Pipeline](rag-pipeline.md) |
| 检索评估 | V0.4.3 | scripts/run_rag_evals.py | [RAG Eval](rag-eval.md) |
| 嵌入层 | V0.4.4 | MockEmbeddingProvider + EmbeddingRegistry | [RAG Embeddings](rag-embeddings.md) |
| 向量存储 | V0.4.5 | InMemoryVectorStore + cosine similarity | [RAG Vector Store](rag-vector-store.md) |
| 检索模式 | V0.4.6 | keyword / vector / hybrid + response metadata | [RAG Retrieval Modes](rag-retrieval-modes.md) |

## 架构

详见 [RAG Runtime Architecture](rag-runtime-architecture.md)。

## 数据合同

详见 [RAG Runtime Contracts](rag-runtime-contracts.md)。

## 评估

详见 [RAG Runtime Eval](rag-runtime-eval.md)。

## 验收

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/check_business_terms.py
cd apps/web && npm run build
```
