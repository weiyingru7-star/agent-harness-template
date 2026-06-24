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

## 当前不实现

- 复杂调度器。
- 多 Agent 协作运行时。
- 生产级 checkpoint。
- 分布式执行。
- Human Review 逻辑。
- 权限系统。
