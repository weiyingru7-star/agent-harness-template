# RAG Vector Store 向量存储层

V0.4.5 为 RAG Pipeline 增加 vector store 抽象层。当前只实现 `InMemoryVectorStore`，不接真实向量数据库。

## 设计目标

- 定义 VectorRecord / VectorSearchRequest / VectorSearchResult / VectorStore interface。
- 实现 InMemoryVectorStore，用于测试 vector store contract。
- 不集成到 ingest 或 retrieve 流程——V0.4.5 只定义接口。
- 不暴露 HTTP API（遵循 V0.4.4 先例）。

## 核心模型

### VectorRecord

```python
class VectorRecord(BaseModel):
    id: str
    vector: list[float]          # embedding 向量
    document_id: str             # 关联文档
    chunk_id: str                # 关联 chunk
    collection: str = "default"
    text: str                    # chunk 文本
    metadata: dict = {}
```

### VectorSearchRequest

```python
class VectorSearchRequest(BaseModel):
    query_vector: list[float]    # 查询向量
    collection: str | None = None
    top_k: int = 10
    metadata_filter: dict | None = None  # 预留
```

### VectorSearchResult

```python
class VectorSearchResult(BaseModel):
    id: str
    document_id: str
    chunk_id: str
    collection: str
    text: str
    score: float                 # cosine similarity（dot product on normalized vectors）
    metadata: dict = {}
```

## VectorStore Interface

```python
class VectorStore(ABC):
    def upsert(self, records: list[VectorRecord]) -> None
    def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]
    def delete(self, ids: list[str]) -> None
    def delete_by_collection(self, collection: str) -> None
    def count(self) -> int
```

## InMemoryVectorStore

dict + collection index 实现：

- `_records: dict[str, VectorRecord]`：ID → record
- `_collection_index: dict[str, set[str]]`：collection → 记录 ID 集合
- `search`：遍历候选记录，计算 dot product，按 score 降序返回 top_k
- `count`：O(1)
- `delete`：O(1)

## 与 MockEmbeddingProvider 配合

```python
provider = MockEmbeddingProvider()
result = provider.embed(EmbeddingRequest(input="chunk text"))
vector = result.embeddings[0]

store = InMemoryVectorStore()
store.upsert([VectorRecord(id="r1", vector=vector, ...)])

results = store.search(VectorSearchRequest(query_vector=vector))
# 相同文本 → 相同 vector → score ≈ 1.0
```

## 与现有 RAG Pipeline 的关系

- keyword retrieve / citation / RAG eval 完全不受影响。
- vector store 不集成到 ingest 或 retrieve。
- InMemoryVectorStore 在测试中按需实例化。

## 验收

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
```
