# How To Create New Agent 如何创建新 Agent

本文档说明如何基于 Agent Harness Template V0 创建一个新的业务模块。模板核心保持业务无关，具体业务逻辑应放在 `modules/{module_name}/` 内。

## 创建新 Agent 模块

在仓库根目录执行：

```bash
python3 cli/scaffold_module.py sample_agent
```

模块名规则：

- 使用小写字母、数字、下划线。
- 必须以字母开头。
- 不要和已有 `modules/` 下的模块重名。

如果模块已存在，脚手架会失败并停止，不会覆盖已有文件。

## 生成目录结构

执行成功后会生成：

```text
modules/sample_agent/
  README.md
  agent.yaml
  evals/
    .gitkeep
  module.yaml
  prompts/
    system.md
  services/
    sample_agent_service.py
  skills/
    .gitkeep
```

## `module.yaml` 的作用

`module.yaml` 描述模块级元信息，例如：

- `id`：模块唯一标识。
- `name`：模块显示名称。
- `description`：模块说明。

模块是能力边界，后续的服务、提示词、局部技能和评测资产都应该放在这个模块目录内。

## `agent.yaml` 的作用

`agent.yaml` 描述 Agent 级元信息，例如：

- `id`：Agent 唯一标识。
- `module_id`：所属模块 ID。
- `name`：Agent 显示名称。
- `description`：Agent 说明。

Agent 是模块内可执行能力的入口描述。V0 只生成最小配置，不自动接入复杂运行时。

## `prompts/` 的作用

`prompts/` 用于存放模块自己的提示词文件。

默认生成：

```text
prompts/system.md
```

建议把稳定的系统提示词放在这里，把临时输入留给调用层传入。

## `services/` 的作用

`services/` 用于存放模块自己的服务逻辑。

默认生成：

```text
services/sample_agent_service.py
```

V0 生成的 service 只是最小占位函数。创建模块后，可以在这里逐步实现模块内部逻辑，再按项目约定接入 API 或运行链路。

## `skills/` 的作用

`skills/` 用于放置模块局部技能定义或说明。

V0 只创建目录和 `.gitkeep`，不会生成远程 skill、插件市场或权限系统。

## `evals/` 的作用

`evals/` 用于存放模块未来可能需要的评测样例或说明。

V0 只创建目录和 `.gitkeep`，不包含 Eval Runner。

## `README.md` 的作用

模块内 `README.md` 用于说明这个模块的目标、目录内容、开发约定和验收方式。

建议在模块开发时补充：

- 模块目标。
- 输入输出约定。
- 本模块依赖的局部资源。
- 本模块的手动验收步骤。

## 创建后的下一步

1. 打开 `modules/sample_agent/README.md`，补充模块目标和边界。
2. 更新 `module.yaml` 和 `agent.yaml` 的描述字段。
3. 编辑 `prompts/system.md`，写入模块自己的中性系统提示词。
4. 在 `services/sample_agent_service.py` 中实现最小可运行逻辑。
5. 如需局部技能说明，放入 `skills/`。
6. 如需评测样例，放入 `evals/`，但 V0 不提供 Eval Runner。
7. 根据需要在后续阶段把模块接入主链路。

## 验收命令

创建模块：

```bash
python3 cli/scaffold_module.py sample_agent
```

确认文件：

```bash
find modules/sample_agent -maxdepth 3 -type f | sort
```

重复创建同名模块：

```bash
python3 cli/scaffold_module.py sample_agent
```

预期结果：

- 第二次命令失败。
- 已有模块不会被覆盖。

运行基础测试：

```bash
make test-api
cd apps/web && npm run build
```

## 注意事项

- 不要把具体业务写进模板核心文档或默认页面。
- 新业务逻辑应放在 `modules/{module_name}/` 内。
- V0 scaffold 不会自动修改 API 路由、registry 或主链路代码。
- V0 scaffold 不会生成 RAG 新功能、LangGraph 新流程、Human Review、多模态或生产级权限能力。
