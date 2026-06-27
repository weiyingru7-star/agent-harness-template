# Guardrail Runtime Integration Plan 护栏运行时集成计划

本文档规划 Policy / Guardrail Runtime 的集成路径，明确从 contract 到
dry-run 再到 future enforcement 的各个阶段。当前 V0.8.6 已完成 input
guardrail dry-run hook，后续将继续实现 tool / provider / RAG 等 hook。
**不修改任何运行时模块**。

## 1. Current State 当前状态

V0.8.0–V0.8.4 已完成所有基础合同和 dry-run 能力：

| 版本 | 交付物 | 状态 |
|---|---|---|
| V0.8.0 | Policy / Guardrail / Rule / Condition 合同、PolicyValidator、JSON Schema | ✅ 完成 |
| V0.8.1 | Policy validation eval runner（`scripts/run_policy_evals.py`）、7 个 eval case | ✅ 完成 |
| V0.8.2 | GuardrailDecision / DecisionResult 合同、决策结构校验 | ✅ 完成 |
| V0.8.3 | EvaluationContext / EvaluationSubject 合同、上下文结构校验 | ✅ 完成 |
| V0.8.4 | PolicyDryRunEvaluator——根据 Policy/Guardrail/Context 生成 DecisionResult。支持 always / match / route condition，expression 安全拒绝 | ✅ 完成 |
| **V0.8.5** | **Runtime 集成计划文档，不修改代码** | 📄 已完成 |
| **V0.8.6** | **Input Guardrail Dry-Run Hook——在 RunStore._create_run 中插入 input dry-run helper** | ✅ 已完成 |
| **V0.8.7** | **Tool Guardrail Dry-Run Hook——在 ToolExecutionPipeline._execute_tool 中插入 tool dry-run helper** | ✅ 已完成 |
| **V0.8.8** | **Provider / RAG Guardrail Dry-Run Helpers——helper 已实现，返回 DecisionResult dict。当前不做 runtime wiring（provider/rag runtime 没有 run_id/trace_id/event_repository）** | ✅ helper 已完成，runtime wiring deferred |

**当前不存在的（明确未来实现）**：

- ❌ 任何 runtime hook（RunStore / ToolExecutionPipeline / Provider / RAG / Workflow）
- ❌ 任何阻止请求的逻辑
- ❌ 任何 middleware
- ❌ 任何新 API endpoint
- ❌ Enforcement engine

## 2. Execution Mode 执行模式

Guardrail system 支持四种执行模式，能力逐级增强：

| Mode | 行为 | V0.8.5 状态 |
|---|---|---|
| `disabled` | Guardrail 不被调用，无任何开销 | ✅ 可通过 config 实现 |
| `validate_only` | 只做结构校验——PolicyValidator 检查 policy/guardrail/context 合同 | ✅ V0.8.0–0.8.3 完成 |
| `dry_run` | 完整 evaluate → 生成 DecisionResult，但不拦截请求 | ✅ V0.8.4 完成 |
| `enforce` | Evaluate + 根据 DecisionResult 拦截/修改请求行为 | 🔮 未来版本 |

```
ExecutionMode 设计示意（不实现）：

class GuardrailConfig:
    mode: str = "validate_only"  # disabled | validate_only | dry_run | enforce
```

**V0.8.5 明确**：当前只支持 `validate_only` 和 `dry_run`。`enforce` 是未来版本的
目标，不在 V0.8.x 中实现。

## 3. Runtime Integration Points 运行时接入点

以下表格列出 guardrail 系统的未来接入点。每个接入点需要：

1. 构建 EvaluationContext
2. 调用 PolicyDryRunEvaluator.evaluate()
3. 根据 ExecutionMode 决定是否对 DecisionResult 做出反应

| 接入点 | 位置 | Scope | Dry-Run 安全 | Enforce 风险 |
|---|---|---|---|---|
| Input guardrail | RunStore.create_run() 前 | input | ✅ 可先行 | 阻止 run 创建会改变 API 行为 |
| Output guardrail | RunStore._create_run() final 后 | output | ✅ 可先行 | 修改/重写 output 需要输出处理 |
| Tool guardrail (before) | ToolExecutionPipeline 执行 tool 前 | tool | ✅ 可先行 | 阻止 tool 执行会影响 run 语义 |
| Tool guardrail (after) | ToolExecutionPipeline tool result 后 | tool | ✅ 可先行 | 修改/过滤 result 需要结果处理 |
| RAG guardrail (before) | Knowledge retrieve 前 | rag | ✅ 可先行 | 阻止/修改 query 会影响检索 |
| RAG guardrail (after) | Knowledge retrieve result 后 | rag | ✅ 可先行 | 过滤/修改结果列表 |
| Provider guardrail (before) | call_provider / smoke 前 | provider | ✅ 可先行 | 阻止 provider 调用会影响所有 LLM 路径 |
| Provider guardrail (after) | Provider response 后 | provider | ✅ 可先行 | 修改/过滤 LLM 输出 |
| Workflow guardrail | Workflow node transition 前/后 | workflow | ✅ 可先行 | 阻止 node 切换影响 workflow 语义 |

### Input Guardrail（示例伪代码）

```python
# V0.8.6 可能的设计 —— 不实现，仅用于说明
def create_run(self, task_input, module_id=None):
    if self.guardrail_mode != "disabled":
        context = self._build_input_context(task_input, module_id)
        result = PolicyDryRunEvaluator.evaluate(
            policies=self.policies,
            guardrails=self.guardrails,
            context=context,
        )
        if self.guardrail_mode == "dry_run":
            log_decision(result)  # 未来：将 decision 记录到 run metadata
        elif self.guardrail_mode == "enforce" and result.final_action == "block":
            raise GuardrailBlocked(result)  # 未来：真正拦截

    return self._create_run(task_input, module_id)
```

## 4. GuardrailDecision Handling 决策处理

| 动作 | Dry-Run 行为 | Enforcement 行为（未来） |
|---|---|---|
| `allow` | 生成 decision，无其他影响 | 继续执行，无其他影响 |
| `warn` | 生成 decision，无其他影响 | 继续执行，记录 warning 到 run events |
| `block` | 生成 decision，**不阻止请求** | **阻止请求**——返回错误或跳过操作 |
| `require_review` | 生成 decision，**不阻止请求** | **路由到人审**——暂停操作，等待决策 |

**V0.8.5 明确**：
- `block` 和 `require_review` 在 dry-run 模式下**不会**阻止或改变请求行为
- Enforcement 实现以上所有动作属于未来版本

## 5. Dry-Run vs Enforcement 区别

| 维度 | Dry-Run (V0.8.4) | Enforcement (未来) |
|---|---|---|
| 生成 DecisionResult | ✅ 已实现 | ✅ 继承 |
| 记录 decision | 🔮 未来 hook 实现 | ✅ 继承 |
| 阻止请求 | ❌ 不会 | 🔮 按 block/require_review 动作 |
| 修改输出 | ❌ 不会 | 🔮 按策略重写/过滤 |
| 路由到人审 | ❌ 不会 | 🔮 暂停 pipeline，等待外部审批 |
| 改变 run status | ❌ 不会 | 🔮 可能设置为 blocked/reviewing |
| 改变 step metadata | ❌ 不会 | 🔮 记录 guardrail decision 引用 |
| 需要真实请求链路 | ❌ 不需要 | ✅ 需要 |

### 关键原则

**Dry-run 是安全、无副作用的。** 它可以在任何上下文中运行而不改变系统状态。
这意味着它可以在 V0.8.6 / V0.8.7 等阶段被嵌入到 runtime 附近，但仍然
**只观察、不干预**。

**Enforcement 需要完整的设计和测试覆盖。** 因为它改变系统行为，需要：
1. 确定的 action 优先级规则（V0.8.4 已实现 final_action merge）
2. 每个接入点的回滚策略
3. 人审集成接口
4. 用户通知机制
5. 完整的测试覆盖

## 6. EvaluationContext Construction 上下文构建

每个接入点需要构建对应 scope 的 EvaluationContext：

| 接入点 | context.subject.type | subject.content / payload 来源 | attributes 来源 |
|---|---|---|---|
| Input | `"run_input"` | task_input | module_id、trace_id |
| Output | `"run_output"` | result.output | run_id、steps 数量 |
| Tool (before) | `"tool_call"` | tool_arguments 序列化 | tool_id、trace_id |
| Tool (after) | `"tool_result"` | tool_call.result.output | tool_id、status、duration_ms |
| RAG (before) | `"rag_query"` | query 文本 | collection、retrieval_mode |
| RAG (after) | `"rag_result"` | citation 文本 | collection、result_count |
| Provider (before) | `"provider_request"` | prompt 文本 | provider_name、model |
| Provider (after) | `"provider_response"` | response.output | provider、latency_ms、usage |
| Workflow | `"workflow_transition"` | node state 序列化 | from_node、to_node、entrypoint |

## 7. Future Version Roadmap 未来版本路线

| 版本 | 内容 | 改 runtime？ | Enforcement？ |
|---|---|---|---|
| **V0.8.5** | Runtime 集成计划文档 | ❌ 不改 | ❌ 不 enforcement |
| **V0.8.6** | Input Guardrail Dry-Run Hook——在 RunStore._create_run 附近调用 dry-run evaluator，记录 decision 但永不阻止 | ⚠️ 仅 dry-run hook | ❌ 不 enforcement |
| **V0.8.7** | Tool Guardrail Dry-Run Hook——在 ToolExecutionPipeline 附近调用 dry-run evaluator | ⚠️ 仅 dry-run hook | ❌ 不 enforcement |
| **V0.8.8** | Provider / RAG Guardrail Dry-Run Helpers——helper 已实现，不接入 runtime | ⚠️ helper 已就绪 | ❌ 不 enforcement |
| V0.8.9 | Guardrail Runtime Docs 收口 | ❌ 不改 | ❌ 不 enforcement |
| Future | Enforcement Engine——真正拦截、阻止、人审 | ✅ 改 | ✅ enforcement |

### V0.8.6–V0.8.9 范围说明

V0.8.6 到 V0.8.9 的 dry-run hook 阶段的约束：

- ✅ **允许**：在现有 pipeline 附近插入 dry-run evaluator 调用
- ✅ **允许**：将 DecisionResult 记录到 run events / step metadata
- ✅ **允许**：新增 eval case 验证 dry-run hook 的行为
- ❌ **禁止**：根据 DecisionResult 阻止或修改请求
- ❌ **禁止**：改变现有 API 响应格式
- ❌ **禁止**：改变 run status 语义
- ❌ **禁止**：要求前置的 enforcement 能力

## 8. Anti-Goals 明确不做的

- ❌ V0.8.5 不修改任何运行时模块（RunStore / ToolExecutionPipeline / Provider / RAG / Workflow）
- ❌ V0.8.5 不新增任何 API endpoint
- ❌ V0.8.5 不实现 enforcement / 阻止逻辑
- ❌ V0.8.5 不接入真实请求链路
- ❌ V0.8.5 不创建业务 Agent

## 9. 相关文档

- [Policy Guardrail Contract](policy-guardrail-contract.md)
- [Tool Execution Pipeline](tool-execution-pipeline.md)
- [Provider Runtime](provider-runtime.md)
- [RAG Runtime](rag-runtime.md)
- [Workflow Contract](workflow-contract.md)
