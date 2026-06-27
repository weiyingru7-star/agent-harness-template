# Policy and Guardrail Contract 策略与护栏合同

V0.8.0 定义业务无关的 Policy / Guardrail Contract，为后续 input guardrail、
output guardrail、tool/rag/provider policy、人审策略打下合同基础。

**V0.8.0 只做 contract / schema / validator / docs / tests。**
不执行 policy，不拦截真实请求，不改变任何运行时行为。

## Motivation 动机

Agent 系统最终需要治理能力：输入校验、输出合规、工具权限、数据访问限制、
人审流程等。Policy / Guardrail Contract 提供统一的声明式结构来描述这些规则，
让未来的执行层可以有据可依。

## Contracts 合同

### Policy 策略

```python
class Policy(BaseModel):
    id: str                       # 唯一标识
    name: str                     # 人类可读的名称
    version: str                  # 合同版本
    scope: str                    # 作用范围（枚举）
    rules: list[Rule]             # 规则列表（可空）
    default_action: str = "allow" # 默认动作
    description: str = ""
    enabled: bool = True
    metadata: dict = {}
```

**scope 枚举**：
- `input` — 输入校验策略
- `output` — 输出合规策略
- `tool` — 工具调用策略
- `rag` — RAG 检索策略
- `provider` — Provider 调用策略
- `workflow` — Workflow 执行策略

**action 枚举**：
- `allow` — 允许（默认）
- `block` — 阻止
- `warn` — 警告
- `require_review` — 需要人工审核

### Guardrail 护栏

```python
class Guardrail(BaseModel):
    id: str                       # 唯一标识
    name: str                     # 人类可读的名称
    type: str                     # 执行点（枚举，与 scope 一致）
    enabled: bool = True
    policy_ref: str | None = None # 关联的 Policy id
    action: str = "allow"         # 默认动作
    metadata: dict = {}
```

**type 枚举**（与 Policy scope 一致）：
`input`, `output`, `tool`, `rag`, `provider`, `workflow`

### Rule 规则

```python
class Rule(BaseModel):
    id: str                       # 唯一标识（必填）
    condition: Condition          # 触发条件（必填）
    action: str = "warn"          # 命中后的动作
    severity: str = "medium"      # 严重程度
    message: str = ""             # 提示信息
    metadata: dict = {}
```

### Condition 条件

```python
class Condition(BaseModel):
    type: str                     # 条件类型（枚举）
    expression: str | None = None # 表达式字符串（不执行）
    match: dict | None = None     # 匹配模式（不执行）
    route_key: str | None = None  # 路由键
    metadata: dict = {}
```

**condition.type 枚举**：
- `always` — 总是触发
- `expression` — 表达式条件（当前不执行）
- `match` — 匹配条件（当前不执行）
- `route` — 路由条件

## Schema 校验规则

### policy.schema.json

| 字段 | 规则 |
|---|---|
| id | 必填，string |
| name | 必填，string |
| version | 必填，string |
| scope | 必填，必须在枚举列表中 |
| default_action | 可选，必须在枚举列表中，默认 `allow` |
| rules | 可选，必须是 array |
| rules[].id | 必填，string |
| rules[].condition | 必填，object |
| rules[].condition.type | 必填，必须在枚举列表中 |
| rules[].action | 可选，必须在枚举列表中 |
| rules[].severity | 可选，必须在枚举列表中 |

### guardrail.schema.json

| 字段 | 规则 |
|---|---|
| id | 必填，string |
| name | 必填，string |
| type | 必填，必须在枚举列表中（与 scope 一致） |
| action | 可选，必须在枚举列表中 |

## PolicyValidator

PolicyValidator 只做**结构校验**：

```
validate_policies(policies) → PolicyValidationResult
validate_guardrails(guardrails, policy_ids) → PolicyValidationResult
```

校验内容：
- scope 必须在允许列表中
- action 必须在允许列表中
- rules 必须是 list
- 每个 rule 必须有 id 和 condition
- condition.type 必须在允许列表中
- severity 必须在允许列表中
- guardrail type 必须在允许列表中
- guardrail policy_ref 不存在时产生 warning（非 error）

**不执行**：expression、match、或任何运行时逻辑。

## PolicyValidationResult

对齐 `WorkflowValidationResult` 的风格：

```python
class PolicyValidationResult(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    error_items: list[PolicyValidationErrorItem]
```

其中 `PolicyValidationErrorItem` 包含 `code`、`message`、`path`（可选）、
`severity`（error / warning）、`metadata`。

## Error Codes 错误码

| Code | Severity | 说明 |
|---|---|---|
| POLICY_ID_MISSING | error | policy 缺少 id |
| POLICY_SCOPE_INVALID | error | scope 不在允许列表中 |
| POLICY_ACTION_INVALID | error | action 不在允许列表中 |
| POLICY_RULES_INVALID | error | rules 必须是 list，rule 必须是 object |
| POLICY_RULE_ID_MISSING | error | rule 缺少 id |
| POLICY_RULE_CONDITION_MISSING | error | rule 缺少 condition |
| POLICY_CONDITION_TYPE_INVALID | error | condition.type 不在允许列表中 |
| POLICY_SEVERITY_INVALID | error | severity 不在允许列表中 |
| GUARDRAIL_ID_MISSING | error | guardrail 缺少 id |
| GUARDRAIL_TYPE_INVALID | error | guardrail type 不在允许列表中 |
| GUARDRAIL_ACTION_INVALID | error | guardrail action 不在允许列表中 |
| GUARDRAIL_POLICY_REF_NOT_FOUND | warning | policy_ref 引用了不存在的 policy id |
| DECISION_ID_MISSING | error | decision 缺少 decision_id |
| DECISION_ACTION_MISSING | error | decision 缺少 action |
| DECISION_ACTION_INVALID | error | decision action 不在允许列表中 |
| DECISION_SEVERITY_INVALID | error | decision severity 不在允许列表中 |
| DECISION_MATCHED_RULES_INVALID | error | matched_rules 不是 list |
| DECISION_RESULT_ACTION_INVALID | error | DecisionResult final_action 不在允许列表中 |
| DECISION_RESULT_DECISIONS_INVALID | error | DecisionResult decisions 不是 list |
| CONTEXT_ID_MISSING | error | evaluation context 缺少 context_id |
| CONTEXT_SCOPE_INVALID | error | scope 不在允许列表中 |
| CONTEXT_SUBJECT_MISSING | error | subject 不存在 |
| CONTEXT_SUBJECT_INVALID | error | subject 不是 object |
| CONTEXT_SUBJECT_TYPE_MISSING | error | subject.type 不存在 |
| CONTEXT_ATTRIBUTES_INVALID | error | attributes 不是 object |

## Agent Template 集成

AgentConfig 新增可选字段：
- `policies: list[dict]` — policy 定义列表
- `guardrails: list[dict]` — guardrail 定义列表

AgentTemplateRegistry.validate_template() 现在也校验 policies 和 guardrails。
没有配置时 valid=true 不变。

### generic_agent 示例

```json
{
  "policies": [],
  "guardrails": [],
  ...
}
```

## 边界说明

### V0.8.1 新增（V0.8.1 不实现以下，保持与 V0.8.0 一致）

- ❌ Condition 表达式执行
- ❌ 真实请求拦截
- ❌ Policy Engine / Guardrail Engine
- ❌ 运行时 middleware
- ❌ 新 API endpoint
- ❌ RunStore / Tool / RAG / Provider / Workflow 改动
- ❌ 业务规则

### V0.8.1 增加

- ✅ PolicyValidationEval runner（`scripts/run_policy_evals.py`）
- ✅ 7 个 eval case（`evals/policy_cases/`）
- ✅ 补齐 4 个稳定 error code

### V0.8.2 增加

- ✅ GuardrailDecision / DecisionResult 数据合同
- ✅ Decision contract 结构校验（`validate_decision_contract` / `validate_decision_result`）
- ✅ 4 个 decision contract eval case
- ✅ 补齐 6 个 decision error code
- ✅ `schemas/guardrail-decision.schema.json`
- ✅ run_policy_evals.py 支持 `decision_contract` 和 `decision_result` 类型

### V0.8.3 增加

- ✅ EvaluationContext / EvaluationSubject 数据合同
- ✅ Context 结构校验（`validate_evaluation_context`）
- ✅ `schemas/policy-evaluation-context.schema.json`
- ✅ 5 个 context contract eval case
- ✅ run_policy_evals.py 支持 `context_contract` 类型

### V0.8.0 不实现（V0.8.1–V0.8.3 同样不实现）

- ❌ Condition 表达式执行
- ❌ 真实请求拦截
- ❌ Policy Engine / Guardrail Engine
- ❌ 运行时 middleware
- ❌ 新 API endpoint
- ❌ RunStore / Tool / RAG / Provider / Workflow 改动
- ❌ 业务规则

## Decision Contract 决策合同

V0.8.2 新增 GuardrailDecision 和 DecisionResult 合同，用于描述 policy / guardrail
结构校验或未来评估后的标准化决策结果。

### GuardrailDecision 单条决策

```python
class GuardrailDecision(BaseModel):
    decision_id: str                    # 唯一标识（必填）
    policy_id: str | None = None        # 关联的 Policy id
    guardrail_id: str | None = None     # 关联的 Guardrail id
    action: str                         # 决策动作（必填）：allow/block/warn/require_review
    severity: str = "medium"            # 严重程度：low/medium/high/critical
    reason: str = ""                    # 决策理由
    matched_rules: list[str] = []       # 匹配的规则 id 列表
    metadata: dict = {}
```

### DecisionResult 决策结果聚合

```python
class DecisionResult(BaseModel):
    valid: bool                         # 决策是否成功解析
    final_action: str = "allow"         # 聚合后的最终动作
    decisions: list[GuardrailDecision] = []  # 所有决策明细
    errors: list[str] = []
    warnings: list[str] = []
    error_items: list[PolicyValidationErrorItem] = []
    metadata: dict = {}
```

### Decision Contract 校验

```python
# 校验单条决策结构
result = PolicyValidator.validate_decision_contract(decision_dict)

# 校验决策结果结构
result = PolicyValidator.validate_decision_result(result_dict)
```

校验规则：
- `decision_id` 必填
- `action` 必填，必须在枚举列表中
- `severity`（如果存在）必须在枚举列表中
- `matched_rules`（如果存在）必须是 list
- `final_action` 必须在枚举列表中
- `decisions` 必须是 list，每个元素递归校验

**不执行**：不根据 input 执行 policy，不生成决策，不调用任何外部系统。

## Evaluation Context Contract 评估上下文合同

V0.8.3 新增 EvaluationContext 合同，用于描述 policy / guardrail 评估时可读取的
上下文结构。未来 dry-run 或 runtime evaluation 可以使用该合同传递上下文信息。

### EvaluationContext 评估上下文

```python
class EvaluationSubject(BaseModel):
    type: str                       # 主体类型（必填）
    id: str | None = None           # 可选主体标识
    content: str | None = None      # 可选文本内容
    payload: dict | None = None     # 可选结构化负载
    metadata: dict = {}

class EvaluationContext(BaseModel):
    context_id: str                 # 上下文标识（必填）
    scope: str                      # 作用范围（必填，与 POLICY_SCOPES 一致）
    subject: EvaluationSubject      # 评估主体（必填）
    attributes: dict = {}           # 中性结构化属性
    metadata: dict = {}
```

### Evaluation Context 校验

```python
result = PolicyValidator.validate_evaluation_context(context_dict)
```

校验规则：
- `context_id` 必填
- `scope` 必填，必须在枚举列表中
- `subject` 必填，必须是 object
- `subject.type` 必填
- `attributes`（如果存在）必须是 object

**不执行**：不根据 context 执行 policy，不生成决策，不调用任何外部系统。

## Policy Dry-Run Evaluator 策略 Dry-Run 评估器

V0.8.4 新增业务无关的 PolicyDryRunEvaluator，根据 Policy / Guardrail /
EvaluationContext 生成 DecisionResult。**不接 runtime，不拦截请求，不 enforcement。**

### 支持的 Condition 类型

| 类型 | 行为 | 说明 |
|---|---|---|
| `always` | 总是匹配 | 按 rule.action 生成 decision |
| `match` | 结构字段匹配 | field dot-notation + equals/contains/exists 操作符 |
| `route` | route_key 存在性匹配 | route_key 在 context.attributes 中存在即匹配 |
| `expression` | **不执行** | 安全 fallback——返回 require_review + unsupported_expression |

### Match 操作符

```text
equals:   context.subject.content == "hello"
contains: "help" in context.subject.content
exists:   "key" in context.attributes
```

### Final Action 合并规则

优先级（从高到低）：`block > require_review > warn > allow`

- 任一 decision 为 block → final_action = block
- 任一 decision 为 require_review（无 block）→ final_action = require_review
- 任一 decision 为 warn（无 block 或 require_review）→ final_action = warn
- 全部为 allow（或无 decision）→ final_action = allow

### Guardrail Policy Ref 解析

| 场景 | 行为 |
|---|---|
| guardrail 有 policy_ref + policy 存在 | 只评估该 policy |
| guardrail 有 policy_ref + policy 不存在 | 返回 require_review + error metadata |
| guardrail 无 policy_ref | 评估所有 scope 匹配的 policy |

### Evaluator 调用

```python
from app.policies.evaluator import PolicyDryRunEvaluator

result = PolicyDryRunEvaluator.evaluate(
    policies=policies,      # list[dict]
    guardrails=guardrails,  # list[dict]
    context=context,        # EvaluationContext dict
)
# result = DecisionResult dict
```

## Dry-Run Hooks 运行时 Hook

V0.8.6 开始将 PolicyDryRunEvaluator 接入 Agent 核心链路。每个 hook
构造对应 scope 的 EvaluationContext，调用 evaluator，记录决策结果。

### Input Guardrail Hook（V0.8.6）

在 `RunStore._create_run` 中 `run.started` 之后、`execute_module` 之前执行：

```python
from app.policies.dry_run_hooks import run_input_guardrail

sequence = run_input_guardrail(
    task_input=task_input,
    run_id=run.id,
    run_metadata=run_metadata,
    trace_id=trace_id,
    sequence=sequence,
    event_repository=event_repository,
    policies=[],      # 需要从 AgentConfig 加载
    guardrails=[],
)
```

### Hook 行为约束

| 约束 | 说明 |
|---|---|
| No-op | 没有 policies/guardrails 时跳过，不记录 event |
| Dry-run only | 生成 DecisionResult 但永不阻止请求 |
| Safe exception | 任何异常被捕获并静默返回，不影响 run 创建 |
| Event type | `guardrail.dry_run.completed` |
| API response | 不改变 `/api/runs` 响应结构 |
| Run status | 不改变 run.status |

## Eval Runner 评估运行器

V0.8.1 新增独立的 policy validation eval runner：

```bash
python3 scripts/run_policy_evals.py
```

### Eval Cases

22 个 eval case 位于 `evals/policy_cases/`：

| Case | Type | 预期 valid | Error / Warning Codes |
|---|---|---|---|
| valid_policy | policy_validation | true | — |
| valid_empty_policy_list | policy_validation | true | — |
| invalid_scope | policy_validation | false | POLICY_SCOPE_INVALID |
| invalid_action | policy_validation | false | POLICY_ACTION_INVALID |
| invalid_condition_type | policy_validation | false | POLICY_CONDITION_TYPE_INVALID |
| invalid_guardrail_type | policy_validation | false | GUARDRAIL_TYPE_INVALID |
| invalid_guardrail_policy_ref | policy_validation | true (warning) | GUARDRAIL_POLICY_REF_NOT_FOUND |
| valid_decision_result | decision_result | true | — |
| invalid_decision_action | decision_contract | false | DECISION_ACTION_INVALID |
| invalid_decision_severity | decision_contract | false | DECISION_SEVERITY_INVALID |
| invalid_decision_missing_action | decision_contract | false | DECISION_ACTION_MISSING |
| valid_input_context | context_contract | true | — |
| valid_tool_context | context_contract | true | — |
| invalid_context_scope | context_contract | false | CONTEXT_SCOPE_INVALID |
| invalid_context_missing_subject | context_contract | false | CONTEXT_SUBJECT_MISSING |
| invalid_context_attributes_type | context_contract | false | CONTEXT_ATTRIBUTES_INVALID |
| dry_run_allow_always | dry_run | true | — |
| dry_run_warn_match | dry_run | true | — |
| dry_run_block_match | dry_run | true | — |
| dry_run_require_review_route | dry_run | true | — |
| dry_run_unsupported_expression | dry_run | true | — |
| dry_run_guardrail_policy_ref_missing | dry_run | true | — |

run_policy_evals.py 遵循与其他 eval runner（run_workflow_evals.py）相同的模式：
加载 JSON → 调用 PolicyValidator / PolicyDryRunEvaluator → 比较 expected_valid /
expected_error_codes / expected_final_action → 输出 PASS / FAIL。

## 示例

### Input length check 输入长度检查

```python
policy = Policy(
    id="input_length_check",
    name="Input Length Check",
    version="1.0.0",
    scope="input",
    rules=[
        Rule(
            id="max_length",
            condition=Condition(
                type="expression",
                expression="len(input) > 1000",
            ),
            action="warn",
            severity="medium",
            message="Input exceeds recommended length",
        ),
    ],
    default_action="allow",
)
```

### Tool allowlist guardrail 工具白名单护栏

```python
guardrail = Guardrail(
    id="tool_allowlist",
    name="Tool Allowlist Guardrail",
    type="tool",
    policy_ref="tool_allowlist_policy",
    action="block",
)
```

## 相关文档

- [Agent YAML Config](agent-yaml-config.md)
- [Example Agent Template](example-agent-template.md)
- [Guardrail Runtime Integration Plan](guardrail-runtime-integration-plan.md)
- [Validation Error Codes](workflow-validation.md)（Policy 错误码独立但风格一致）
