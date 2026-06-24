# Observability

本文档说明当前可观察性能力和未来边界。

## 当前能力

V0.1.0 已提供最小可观察性：

- Run 状态。
- Step 记录。
- Event 记录。
- 状态机节点事件。

这些能力用于本地开发和基础验收。

## 未来方向

`core/observability/` 和 `harness/events/` 可在未来承载：

- 统一日志格式。
- 指标约定。
- trace id。
- request id。
- event schema。
- 外部观测平台适配。

## 当前不实现

- 外部 tracing 平台。
- metrics server。
- 日志聚合。
- 告警系统。
- 生产级审计。
