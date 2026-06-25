# RAG Contracts RAG 数据契约

V0.4.0 强化了 Document / Chunk / Citation / RetrievalResult 数据契约。

## Document

```python
class Document(BaseModel):
    id: str
    file_id: str
    filename: str
    source_type: str = "file"
    collection: str | None = None     # 文档集合名称，默认 "default"
    title: str | None = None          # 文档标题
    source: str | None = None         # 文档来源标签
    content_type: str | None = None   # 原始内容类型
    created_at: datetime
```

通过 `POST /api/knowledge/ingest` 创建，通过 `GET /api/knowledge/documents` 和 `GET /api/knowledge/documents/{document_id}` 查询。

## Chunk

```python
class Chunk(BaseModel):
    id: str
    document_id: str
    file_id: str
    text: str
    index: int
    collection: str | None = None     # 从文档继承
    char_count: int = 0               # 字符数
    token_count: int = 0              # 近似 token 数（space-split）
    created_at: datetime
```

通过 `GET /api/knowledge/collections/{collection}/chunks` 按集合查询。

## Citation

```python
class Citation(BaseModel):
    document_id: str
    chunk_id: str
    file_id: str
    filename: str
    chunk_index: int
    title: str | None = None          # 源文档标题
    source: str | None = None         # 源文档来源标签
    quote: str | None = None          # 匹配文本片段（前200字符）
    score: int = 0                    # 检索匹配分数
    collection: str | None = None     # 从文档级联
```

通过 `POST /api/knowledge/retrieve` 的 `results[i].citation` 获得。

## RetrievalResult

```python
class RetrieveResponse(BaseModel):
    query: str
    results: list[RetrieveResult]     # 每个含 chunk + score + citation
```

## 文件位置

- 模型定义：`harness/rag/models.py`
- Schema 契约：`schemas/document.schema.json`、`schemas/chunk.schema.json`、`schemas/citation.schema.json`、`schemas/retrieval-result.schema.json`
- 存储操作：`harness/rag/store.py`
- 分块逻辑：`harness/rag/chunking.py`
