# Agent Runtime

本文档说明 V0.1.0 已实现的 Agent Run 主链路，以及 V0.1.1 对 runtime 目录的定位。

## 当前能力

V0.1.0 已实现最小 Agent Run 主链路：

- 创建 Run。
- 执行通用 demo agent。
- 记录 Step。
- 记录 Event。
- 查询 Run。
- 查询 Run Events。

V0.1.8 增强了 Module Registry 和 Agent Execution Contract：

- `modules/*/module.yaml` 可被扫描。
- `modules/*/agent.yaml` 可被读取。
- `POST /api/runs` 不传 `module_id` 时继续默认运行 `demo_agent`。
- `POST /api/runs` 传 `module_id` 时尝试运行对应模块。
- 模块入口统一为 `execute(input_text, context)`。

V0.2.1 增强了 Trace / Event Contract：

- 每次 Run 生成 `trace_id`。
- 每个 node step 生成 `span_id`。
- Event 保留旧字段，同时增加 typed event 字段。
- 新增 `GET /api/runs/{run_id}/trace`，用于后续 timeline、debug 和 eval。

V0.2.2 增强了 Checkpoint Runtime：

- 每个 completed step 后保存一次 state snapshot。
- `demo_agent` 成功运行会产生 input / skill / tool / final 四个 checkpoint。
- checkpoint 只用于 debug、后续 resume 和 eval trajectory 的基础，不实现恢复。

V0.2.3 增强了 Failure / Retry Runtime：

- failed run 会记录 `error_type`、`error_message`、`failed_at`。
- failed step 会记录 attempt 和错误字段。
- events 会记录 `step.failed` 和 `run.failed`。
- `POST /api/runs/{run_id}/retry` 可以手动重试 failed run。
- retry 会生成新的 run，不覆盖旧 run，也不从 checkpoint 恢复。

API 保持：

```text
POST /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/events
```

## Runtime 边界

`harness/runtime/` 是未来通用运行时目录。V0.1.1 只补齐目录说明，不移动现有 Run 代码，不改变 API 行为。

未来 runtime 可承载：

- 执行上下文。
- 生命周期管理。
- 运行状态流转。
- Step / Event 统一协议。
- 模块执行适配。

## Agent Execution Contract

最小入口：

```python
def execute(input_text, context):
    ...
```

最小返回：

```text
AgentExecutionResult
  output
  steps
  metadata
```

`steps` 用于继续写入 Run Step 和 Event。V0.1.8 不改变现有 Step / Event API。

## API 兼容

旧请求继续有效：

```json
{"input":"hello"}
```

显式选择模块：

```json
{"input":"hello","module_id":"demo_agent"}
```

事件接口保持兼容：

```text
GET /api/runs/{run_id}/events
```

Trace 查询接口：

```text
GET /api/runs/{run_id}/trace
```

Checkpoint 查询接口：

```text
GET /api/runs/{run_id}/checkpoints
GET /api/checkpoints/{checkpoint_id}
```

Retry 接口：

```text
POST /api/runs/{run_id}/retry
```

## 当前不实现

- 复杂调度器。
- 多 Agent 协作运行时。
- 生产级 checkpoint。
- 分布式执行。
- Human Review 逻辑。
- 权限系统。
