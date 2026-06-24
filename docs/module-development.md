# Module Development

模块是 Agent Harness Template 承载具体能力的边界。模板核心保持通用，具体逻辑应放在 `modules/{module_name}/` 内。

## 创建模块

使用脚手架：

```bash
python3 cli/scaffold_module.py sample_agent
```

脚手架会阻止覆盖已有模块。

## 标准结构

```text
modules/sample_agent/
  README.md
  module.yaml
  agent.yaml
  prompts/
    system.md
  services/
    sample_agent_service.py
  skills/
    .gitkeep
  evals/
    .gitkeep
```

## 文件职责

- `module.yaml`：模块元信息。
- `agent.yaml`：Agent 元信息。
- `prompts/`：模块提示词。
- `services/`：模块服务逻辑。
- `skills/`：模块局部技能说明或资产。
- `evals/`：模块局部评测资产。
- `README.md`：模块说明。

## Schema 参考

V0.1.3 为模块配置补齐了最小 schema 草案：

- `module.yaml` 应参考 `schemas/module.schema.json`。
- `agent.yaml` 应参考 `schemas/agent.schema.json`。

这些 schema 是通用契约草案，不会自动校验现有文件，也不会改变现有 API 行为。模块配置可以在模块目录内扩展，但不应把模块自己的逻辑写进底座核心目录。

## 开发建议

- 先明确模块边界。
- 保持模板核心业务无关。
- 把模块自己的提示词、服务、技能和评测资产放在模块目录内。
- 需要接入主链路时，再按明确阶段改造 API 或 registry。

## 当前不实现

- 自动注册新模块。
- 复杂模板引擎。
- AST 修改。
- Eval Runner。
- 远程 skill。
- 插件市场。
