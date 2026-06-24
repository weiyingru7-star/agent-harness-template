# Workflow Execution

本文档说明 V0.1.0 的最小状态机能力，以及 V0.1.1 对 workflow 目录的定位。

## 当前能力

V0.1.0 已实现 demo agent 的最小可观察状态机：

- `input_node`
- `skill_node`
- `tool_node`
- `final_node`

每个节点执行都会记录到 Run Step / Event。

当前代码位置：

```text
harness/state_machine/
```

## Workflow 目录定位

`harness/workflow/` 是未来 workflow execution 的蓝图目录。V0.1.1 不移动 `harness/state_machine/`，不升级复杂 workflow planner。

未来这里可承载：

- 通用 workflow 定义。
- 节点协议。
- 执行策略。
- 状态传递约定。
- 可观察性钩子。

## 当前不实现

- 复杂 planner。
- 生产级 checkpoint。
- 分布式 workflow。
- 可视化编排器。
- Human Review 节点逻辑。
