# CLI / Scaffold Usage Guide CLI 脚手架使用指南

本指南介绍 V0.9 CLI / Scaffold 系统提供的四个命令，包括参数说明、
dry-run 示例、正常生成示例、force 覆盖示例和验收方式。

## Prerequisites 前置条件

- Python 3.11+
- 项目依赖已安装：`make install-api`
- 当前目录为项目根目录

## Commands 命令

### 1. Scaffold Module 生成模块

```bash
python3 scripts/scaffold_module.py --help
```

**Dry-run** — 预览将生成的文件：

```bash
python3 scripts/scaffold_module.py --name sample_module --dry-run
```

输出：

```
Generated files:
  modules/sample_module/module.yaml
  modules/sample_module/agent.yaml
  modules/sample_module/README.md
  modules/sample_module/services/sample_module_service.py
  modules/sample_module/prompts/system.md
  modules/sample_module/skills/.gitkeep
  modules/sample_module/evals/.gitkeep

[dry-run] No files were written.
```

**Normal** — 生成模块骨架：

```bash
python3 scripts/scaffold_module.py --name sample_module
```

**Force** — 覆盖已存在的模块目录：

```bash
python3 scripts/scaffold_module.py --name sample_module --force
```

**生成位置**: `modules/<module_name>/`

**验收**:
```bash
ls modules/sample_module/
make test-api
```

### 2. Scaffold Agent Template 生成 Agent 模板

```bash
python3 scripts/scaffold_agent.py --help
```

**Dry-run**:

```bash
python3 scripts/scaffold_agent.py --name sample_agent --dry-run
```

输出：

```
Generated files:
  templates/sample_agent/agent.json
  templates/sample_agent/README.md

[dry-run] No files were written.
```

**Normal**:

```bash
python3 scripts/scaffold_agent.py --name sample_agent
```

**Force**:

```bash
python3 scripts/scaffold_agent.py --name sample_agent --force
```

**生成位置**: `templates/<agent_name>/`

**验收**:
```bash
ls templates/sample_agent/
# 启动 API 后通过 API 验证
curl http://localhost:8005/api/agent-templates/sample_agent | python3 -m json.tool
```

### 3. Scaffold Eval Case 生成 Eval Case

```bash
python3 scripts/scaffold_eval.py --help
```

**Dry-run**:

```bash
python3 scripts/scaffold_eval.py --name sample_eval --dry-run
```

输出：

```
Generated file:
  evals/cases/sample_eval.json

[dry-run] No files were written.
```

**Normal**:

```bash
python3 scripts/scaffold_eval.py --name sample_eval
```

**Force**:

```bash
python3 scripts/scaffold_eval.py --name sample_eval --force
```

**生成位置**: `evals/cases/<eval_name>.json`

**验收**:
```bash
ls evals/cases/sample_eval.json
python3 -c "import json; json.load(open('evals/cases/sample_eval.json')); print('Valid JSON')"
```

### 4. Scaffold Docs 生成文档骨架

```bash
python3 scripts/scaffold_docs.py --help
```

**Dry-run**:

```bash
python3 scripts/scaffold_docs.py --name sample_docs --kind generic --dry-run
```

**Normal**:

```bash
python3 scripts/scaffold_docs.py --name sample_docs --kind generic
```

**Force**:

```bash
python3 scripts/scaffold_docs.py --name sample_docs --kind generic --force
```

**生成位置**: `docs/scaffolds/<kind>-<name>.md`

**验收**:
```bash
ls docs/scaffolds/
```

## Common Options 通用参数

| 参数 | 适用命令 | 说明 |
|---|---|---|
| `--name NAME, -n NAME` | 全部 | 名称，snake_case（必填） |
| `--kind {module,agent,eval,generic}` | `scaffold_docs` | 文档类型，默认 `generic` |
| `--dry-run` | 全部 | 预览文件列表，不写入 |
| `--preview` | 全部 | `--dry-run` 别名 |
| `--force` | 全部 | 覆盖已存在的目标 |

## Safety Notes 安全说明

- 所有 scaffold 命令默认拒绝覆盖已存在的目标
- `--force` 只能覆盖 scaffold 管理的目标目录或文件
- 目标路径被严格限制在 `modules/`、`templates/`、`evals/cases/`、`docs/scaffolds/` 下
- 命名校验拒绝敏感词（`.env`、`secret`、`key` 等）和业务词
- 生成的骨架默认使用 mock provider，不含 API key
