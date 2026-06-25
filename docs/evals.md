# Evals

本文档说明 evals 的目录定位和 V0.2.5 最小 Eval Trajectory Runner。

## 目录

根级目录：

```text
evals/
```

模块级目录：

```text
modules/{module_name}/evals/
```

## 用途

evals 可用于存放：

- 输入样例。
- 预期输出说明。
- 回归检查清单。
- 手动验收材料。
- 模块级评测说明。

## 当前状态

V0.2.5 已新增最小 eval runner：

```bash
python3 scripts/run_evals.py
```

runner 会读取：

```text
evals/cases/*.json
```

并通过现有 run execution API 检查：

- run status。
- output 包含预期文本。
- events 包含预期 event type。
- steps 包含预期 step name。
- trace spans 数量。
- checkpoints 数量。
- timeline items 数量。

详细说明见：

- [Eval Trajectory](eval-trajectory.md)

## 当前不实现

- 真实模型评测。
- LLM-as-judge。
- 复杂评分系统。
- 外部评测平台接入。
- 生产级质量门禁。
