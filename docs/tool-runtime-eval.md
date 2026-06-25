# Tool Runtime Eval Cases 评估用例

V0.2.5 引入 Eval Trajectory runner，V0.3.x 为其增加了 tool 级的 eval cases。本文档汇总全部 8 个 eval case。

## 运行方式

```bash
python3 scripts/run_evals.py
```

每个 case 使用 FastAPI `TestClient` 和临时 SQLite 数据库，不依赖本地 API 服务器或 PostgreSQL。

## Eval Cases 一览

| case id | 输入 | 触发路径 | 验证点 |
|---|---|---|---|
| `demo_agent_success` | `"hello eval trajectory"` | 正常执行 | status=completed, tool_calls_min=1, events 含 `tool.call.completed` |
| `demo_agent_failure` | `"hello eval __fail__"` | `__fail__` → skill_node 失败，run failed | status=failed, tool_calls_min=0, 无 tool_call |
| `demo_agent_invalid_tool_args` | `"hello eval __invalid_tool_args__"` | args 校验失败 | tool_call.status=failed, error_type=ToolArgsValidationError, run still completed |
| `demo_agent_tool_exception` | `"hello eval __tool_exception__"` | 工具抛异常 | tool_call.status=failed, error_type=ToolExecutionError, events 含 tool.call.failed |
| `demo_agent_tool_timeout` | `"hello eval __slow_tool__"` | 超时 | tool_call.status=failed, error_type=ToolTimeoutError, duration_ms ≥ 900 |
| `demo_agent_flaky_tool_retry` | `"hello eval __flaky_tool__"` | 首次失败→重试→成功 | tool_call.status=completed, retry_count=1, attempts 长度=2 |
| `demo_agent_tool_permission_denied` | `"hello eval __restricted_tool__"` | 权限拒绝 | tool_call.status=failed, error_type=ToolPermissionDenied, result.status=failed |
| `demo_agent_tool_sandbox_blocked` | `"hello eval __sandbox_blocked__"` | sandbox 拒绝 | tool_call.status=failed, error_type=ToolSandboxViolation, events 含 tool.call.failed |

## 各 Case 校验项

每个 case 校验以下维度（由 `scripts/run_evals.py` 的 `run_eval_case` 函数执行）：

| 校验项 | 说明 |
|---|---|
| expected_status | run.status 匹配 `"completed"` 或 `"failed"` |
| expected_output_contains | run.output 包含预期文本片段 |
| expected_events | 所有列出的 event_type 都存在 |
| expected_steps | 所有列出的 step name 都存在 |
| expected_checkpoints_min | checkpoints 数量 ≥ 最小值 |
| expected_trace_spans_min | trace.spans 数量 ≥ 最小值 |
| expected_timeline_items_min | timeline.items 数量 ≥ 最小值 |
| expected_tool_calls_min | tool_calls 数量 ≥ 最小值 |
| 如果 expected_status = failed | 校验 failed step 存在且有 error_type；timeline 有 failed item 且有 error_type |

## 测试触发词表

| 触发词 | 作用于 | 效果 |
|---|---|---|
| （无） | tool_node | 正常执行，ToolResult.completed |
| `__fail__` | skill_node | skill 失败，run failed（V0.2.3） |
| `__invalid_tool_args__` | tool_node | args 校验失败（V0.3.1） |
| `__tool_exception__` | tool_node | 工具抛异常被捕获（V0.3.2） |
| `__slow_tool__` | tool_node | 超时触发 ToolTimeoutError（V0.3.3） |
| `__flaky_tool__` | tool_node | 首次失败→重试→成功（V0.3.4） |
| `__restricted_tool__` | tool_node | 权限拒绝（V0.3.5） |
| `__blocked_tool__` | tool_node | 权限拒绝（V0.3.5） |
| `__sandbox_blocked__` | tool_node | sandbox 拒绝（V0.3.6） |

## 预期输出

```
PASS demo_agent_failure
PASS demo_agent_flaky_tool_retry
PASS demo_agent_invalid_tool_args
PASS demo_agent_success
PASS demo_agent_tool_exception
PASS demo_agent_tool_permission_denied
PASS demo_agent_tool_sandbox_blocked
PASS demo_agent_tool_timeout
Summary: 8 passed, 0 failed, 8 total
```

## 文件位置

- eval cases: `evals/cases/*.json`
- eval runner: `scripts/run_evals.py`
- eval 测试: `apps/api/tests/test_eval_runner.py`
