# RAG Retrieval Modes 检索模式

V0.4.6 为 RAG retrieve 增加 `retrieval_mode` 合同，支持 keyword / vector / hybrid 三种模式。

## 请求字段

`POST /api/knowledge/retrieve` 新增可选字段：

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `retrieval_mode` | string | `"keyword"` | `"keyword"` / `"vector"` / `"hybrid"` |
| `collection` | string \| null | null | vector 模式时用于集合过滤 |

## 三种模式

### keyword（默认）

与 V0.4.0–0.4.5 完全一致的关键词计数检索。不传 `retrieval_mode` 时走此路径。

- 算法：查询词在 chunk 中的出现次数
- score_type: `term_frequency`
- 零外部依赖

### vector

使用 V0.4.4 `MockEmbeddingProvider` + V0.4.5 `InMemoryVectorStore` 的向量检索。

- 算法：cosine similarity（dot product on normalized vectors）
- score：`int(cosine * 100)`，score_type: `"cosine"`
- 惰性建索引：首次 vector 请求时从 DB chunks 构建内存向量索引
- 不接真实向量库，不接真实 embedding API

### hybrid

keyword + vector 结果去重合并（vector 优先）。

- 不实现复杂权重融合
- 不实现 rerank
- 结果去重：按 chunk_id 去重，vector 结果优先

## 响应 metadata

`RetrieveResponse` 新增 `metadata` 字段：

```json
{
  "retrieval_mode": "vector",
  "score_type": "cosine"
}
```

`RetrieveResult` 新增 `retrieval_mode` / `score_type` 字段，与 metadata 保持一致。

## 兼容性

- 不传 `retrieval_mode` → keyword → V0.4.0–0.4.5 行为完全一致
- 所有已有测试 / eval 通过
- ingest 不受影响

## 验收

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
```
