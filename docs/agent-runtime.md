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

## 当前不实现

- 复杂调度器。
- 多 Agent 协作运行时。
- 生产级 checkpoint。
- 分布式执行。
- Human Review 逻辑。
- 权限系统。
