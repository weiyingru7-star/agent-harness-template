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

### V0.8.0 只做

- ❌ Condition 表达式执行
- ❌ 真实请求拦截
- ❌ Policy Engine / Guardrail Engine
- ❌ 运行时 middleware
- ❌ 新 API endpoint
- ❌ RunStore / Tool / RAG / Provider / Workflow 改动
- ❌ 业务规则

### V0.8.0 只做

- ✅ Policy / Guardrail / Rule / Condition 数据合同
- ✅ JSON Schema
- ✅ PolicyValidator（结构校验）
- ✅ AgentTemplate 集成（可选字段，不改变已有行为）
- ✅ 文档和测试

## Eval Runner 评估运行器

V0.8.1 新增独立的 policy validation eval runner：

```bash
python3 scripts/run_policy_evals.py
```

### Eval Cases

7 个 eval case 位于 `evals/policy_cases/`：

| Case | 预期 valid | Error / Warning Codes |
|---|---|---|
| valid_policy | true | — |
| valid_empty_policy_list | true | — |
| invalid_scope | false | POLICY_SCOPE_INVALID |
| invalid_action | false | POLICY_ACTION_INVALID |
| invalid_condition_type | false | POLICY_CONDITION_TYPE_INVALID |
| invalid_guardrail_type | false | GUARDRAIL_TYPE_INVALID |
| invalid_guardrail_policy_ref | true (warning) | GUARDRAIL_POLICY_REF_NOT_FOUND |

run_policy_evals.py 遵循与其他 eval runner（run_workflow_evals.py）相同的模式：
加载 JSON → 调用 PolicyValidator → 比较 expected_valid / expected_error_codes →
输出 PASS / FAIL。

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
- [Validation Error Codes](workflow-validation.md)（Policy 错误码独立但风格一致）
