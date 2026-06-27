# RAG Tenant Filter RAG 租户过滤

V1.4 为 RAG 检索增加了最小 tenant-level 过滤能力。
tenant_id 存储在已有的 metadata JSON 列中，无数据库迁移。

## V1.4 范围

### 当前支持

- ✅ Document metadata 支持 `tenant_id`
- ✅ Chunk chunk_metadata 支持 `tenant_id`
- ✅ Ingestion（`POST /api/knowledge/documents`、`POST /api/knowledge/ingest`）接受可选 `tenant_id`
- ✅ Retrieval（`POST /api/knowledge/retrieve`）接受可选 `tenant_id`
- ✅ Keyword / Vector / Hybrid 三种模式都支持 `tenant_id` 过滤
- ✅ `tenant_id=None` 时保持向后兼容（返回所有 chunks）
- ✅ `tenant_id` 不存在时返回空结果
- ✅ 旧无 tenant_id 的文档仍可检索

### 当前不支持

- ❌ Auth / OAuth / JWT
- ❌ RBAC / 角色级文档访问
- ❌ 部门级文档权限
- ❌ 用户级文档 ACL
- ❌ Tool permission guard（V1.5）

## 数据存储

| 组件 | 存储位置 |
|---|---|
| Document metadata | `DocumentRecord.metadata_` JSON 列（`{"tenant_id": "t1"}`）|
| Chunk metadata | `ChunkRecord.metadata_` JSON 列 → `Chunk.chunk_metadata` |

无需数据库迁移——均为已有 JSON 列。

## 检索过滤行为

| 场景 | 行为 |
|---|---|
| `tenant_id=None`（默认） | 返回所有 chunks，包括有 tenant_id 的 |
| `tenant_id="t1"` | 只返回 `metadata.tenant_id == "t1"` 的 chunks |
| `tenant_id` 不存在 | 返回空结果 |

**重要**：未标记 tenant_id 的 chunks 对所有检索可见（包括 tenant-aware 检索）。
如果要完全隔离，必须确保所有文档在 ingestion 时携带 tenant_id。

## API 使用示例

```bash
# 写入带 tenant_id 的文档
curl -X POST http://localhost:8005/api/knowledge/documents \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Tenant A Doc",
    "text": "This document belongs to tenant A.",
    "tenant_id": "tenant_a"
  }'

# 按 tenant_id 检索
curl -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "document",
    "tenant_id": "tenant_a"
  }'

# 不传 tenant_id 的旧写法仍然可用
curl -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query": "document"}'
```

## 后续版本

| 版本 | 内容 |
|---|---|
| V1.5 | Tool Permission / Ownership Guard |
| V1.6 | Concurrency / Idempotency Contract |
