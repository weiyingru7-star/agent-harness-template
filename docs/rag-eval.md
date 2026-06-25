# RAG Eval 检索评估

V0.4.3 新增最小 RAG 评估能力，通过结构化 eval case 验证 retrieve 是否命中预期 document / chunk / citation。不做 LLM judge、不做复杂指标、不接 embedding 或向量库。

## 设计目标

- 结构化、可复现的 RAG 检索评估。
- 每个 eval case 定义测试文档 + 检索查询 + 预期结果。
- 独立 runner `scripts/run_rag_evals.py`，不影响已有 agent trajectory eval。
- 使用 FastAPI `TestClient` + 临时 SQLite 数据库，不依赖本地服务器或 PostgreSQL。

## Eval Case 格式

```json
{
  "id": "retrieve_checkpoint_title",
  "name": "Retrieve Checkpoint Title",
  "documents": [
    {
      "title": "Agent Checkpoints",
      "text": "Runtime records checkpoints after each completed node...",
      "source": "eval"
    }
  ],
  "queries": [
    {
      "query": "checkpoints",
      "expected_min_results": 1,
      "expected_document_title": "Agent Checkpoints",
      "expected_source": "eval",
      "expected_chunk_contains": "state snapshot",
      "expected_min_score": 1
    }
  ]
}
```

## Runner 行为

1. `reset_db()` 清理数据库
2. 对每个 case：
   - `POST /api/knowledge/documents` 创建所有测试文档
   - 对每个 query：`POST /api/knowledge/retrieve`
   - 校验：结果数、命中文档标题、来源标签、chunk 文本片段、最低分数
3. 输出 PASS / FAIL + Summary

## 运行方式

```bash
python3 scripts/run_rag_evals.py
```

预期输出：

```
PASS retrieve_checkpoint_title
PASS retrieve_tool_call_title
Summary: 2 passed, 0 failed, 2 total
```

## Case 文件

位于 `evals/rag_cases/*.json`。

## 当前 Cases

| case id | 查询词 | 预期命中文档 |
|---|---|---|
| `retrieve_checkpoint_title` | "checkpoints" | "Agent Checkpoints" |
| `retrieve_tool_call_title` | "ToolCall" | "Tool Call Contract" |

## 未来能力

- LLM judge 评估检索质量
- 复杂 RAGAS 指标
- Embedding + 向量库场景下的检索评估
- Rerank 后的评估
