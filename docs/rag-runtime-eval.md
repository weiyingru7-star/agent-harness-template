# RAG Runtime Eval 评估

V0.4.3 引入的 RAG 评估能力。使用结构化 eval case 验证 retrieve 是否命中预期 document / chunk / citation。

## 运行方式

```bash
python3 scripts/run_rag_evals.py
```

## Eval Cases

| case id | 创建文档 | 查询词 | 预期命中文档 | 验证点 |
|---|---|---|---|---|
| `retrieve_checkpoint_title` | Agent Checkpoints + Tool Call Contract | `"checkpoints"` | Agent Checkpoints | min_results=1, source=eval, chunk_contains="state snapshot" |
| `retrieve_tool_call_title` | Agent Checkpoints + Tool Call Contract | `"ToolCall"` | Tool Call Contract | min_results=1, source=eval, chunk_contains="arguments" |

## 触发词汇总

| 触发词 | 作用于 | 效果 |
|---|---|---|
| "checkpoints" | retrieve | 命中 "Agent Checkpoints" 文档 |
| "ToolCall" | retrieve | 命中 "Tool Call Contract" 文档 |

## Runner 行为

1. `reset_db()` 清理数据库
2. 对每个 case：
   - `POST /api/knowledge/documents` 创建所有测试文档
   - 对每个 query：`POST /api/knowledge/retrieve`
   - 校验：结果数、命中文档标题、来源标签、chunk 文本片段、最低分数
3. 输出 PASS / FAIL + Summary

## 预期输出

```
PASS retrieve_checkpoint_title
PASS retrieve_tool_call_title
Summary: 2 passed, 0 failed, 2 total
```

## 文件位置

- eval cases: `evals/rag_cases/*.json`
- eval runner: `scripts/run_rag_evals.py`
