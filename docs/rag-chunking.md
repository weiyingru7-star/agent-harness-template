# RAG Chunking Strategy

V0.4.1 增强了 RAG Pipeline 的文档切分策略，支持可配置的 chunk_size、chunk_overlap、按段落优先切分、超长段落 fallback。

## ChunkingConfig

```python
class ChunkingConfig(BaseModel):
    chunk_size: int = 500          # 目标分块字符数上限（50–4000）
    chunk_overlap: int = 0         # 相邻 chunk 重叠字符数（0–500）
    split_by: str = "paragraph"    # "paragraph" | "fixed_chars"
    preserve_paragraphs: bool = True
    min_chunk_size: int = 50       # 最小有效 chunk（低于此值与前一个合并）
```

## 算法流程

### paragraph（默认）

```
text
  → split by "\n\n" → paragraphs
  → 对每段：
    - 段长 < min_chunk_size → 追加到当前 buffer
    - 段长 ≤ chunk_size     → 追加到当前 buffer（保持 \n\n 分隔）
    - 段长 > chunk_size × 1.2 → flush buffer, fallback fixed_chars
  → 超长段落按 fixed_chars 切分
  → 如有 chunk_overlap > 0 → 后处理
```

### fixed_chars

```
text → 按 chunk_size 固定窗口切分 → overlap 后处理
```

## Overlap 实现

后处理模式：先完成基础切分，再对每个非首个 chunk 前缀追加前一个 chunk 末尾的文本。

```python
for i ≥ 1:
    overlap_suffix = chunks[i-1][-overlap:]
    chunks[i] = overlap_suffix + chunks[i]
```

overlap 后的 chunk 记录 `overlap_with_previous` 表示重叠字符数。

## Chunk metadata

每个 chunk 的 `chunk_metadata` 包含：

| 字段 | 类型 | 含义 |
|---|---|---|
| start_char | int | 在源文本中的起始偏移 |
| end_char | int | 在源文本中的结束偏移 |
| split_strategy | str | 该 chunk 的切分策略（paragraph / fixed_chars） |
| overlap_with_previous | int | 与前一个 chunk 的重叠字符数（首个为 0） |
| chunk_size | int | 该 chunk 使用的 chunk_size 配置 |
| chunk_overlap | int | 该 chunk 使用的 chunk_overlap 配置 |

存储在 `ChunkRecord.metadata_` JSON 列中。

## API 使用

POST `/api/knowledge/ingest` 支持可选字段 `chunking_config`：

```json
{
  "file_id": "<file_id>",
  "chunking_config": {
    "chunk_size": 300,
    "chunk_overlap": 50,
    "split_by": "paragraph"
  }
}
```

不传 `chunking_config` 时使用默认策略（chunk_size=500, overlap=0, paragraph-first），行为与 V0.4.0 一致。

## 验收

```bash
make test-api
python3 scripts/run_evals.py
```
