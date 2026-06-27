# CLI / Scaffold Contract CLI 与脚手架合同

V0.9.0 设计 CLI / Scaffold 方案，让用户可以快速创建新的 agent / module 模板。
**本阶段只做 contract / plan / docs，不实现复杂 CLI。**

## 1. Motivation 动机

创建新 agent 或 module 时，开发者需要手动复制模板目录、替换占位符、创建测试骨架。
这个过程耗时且容易出错。CLI / Scaffold 工具可以自动化这一过程，让开发者专注于
业务逻辑而非重复的文件操作。

## 2. Existing State 现有状态

### scaffold_module.py (V0.5c)

当前已存在最小可用的 module scaffold 脚本：

- **文件**: `cli/scaffold_module.py`
- **功能**: 从 `templates/module-template/` 复制文件到 `modules/<name>/`，替换
  `{{module_name}}` 和 `{{module_title}}` 占位符
- **校验**: module 名称必须匹配 `^[a-z][a-z0-9_]*$`，不能覆盖已有模块
- **测试**: `apps/api/tests/test_scaffold_module.py`（3 条测试）
- **生成物**:
  - `modules/<name>/module.yaml`
  - `modules/<name>/agent.yaml`
  - `modules/<name>/services/__module_name___service.py`
  - `modules/<name>/prompts/system.md`
  - `modules/<name>/skills/.gitkeep`
  - `modules/<name>/evals/.gitkeep`
  - `modules/<name>/README.md`

**当前不足**：没有 dry-run mode、没有 `--force`、没有 agent template scaffold、
没有 eval case scaffold。

## 3. Command Design 命令设计

### Level 1 — Current（V0.5c）

```bash
python3 cli/scaffold_module.py <module_name>
```

### Level 2 — Proposed（V0.9.1–V0.9.3）

```bash
python3 scripts/scaffold.py --help
python3 scripts/scaffold.py module <name>     # scaffold a module
python3 scripts/scaffold.py agent <name>       # scaffold an agent template
python3 scripts/scaffold.py eval <name>        # scaffold eval cases
```

### Level 3 — Future（not committed）

```bash
agent-harness scaffold module <name>
```

Level 3 取决于项目成熟度，**当前不承诺实现**。

## 4. Scaffold Output 生成物

| Subcommand | Generates | Source Template | Status |
|---|---|---|---|
| `module <name>` | `modules/<name>/` — YAML config, service stub, prompts, evals, skills, README | `templates/module-template/` | ✅ Exists (V0.5c) |
| `agent <name>` | `templates/<name>/` — agent.json, README | `templates/agent-template/` | 📝 Proposed |
| `eval <name>` | `evals/cases/<name>.json` + stub | Template TBD | 📝 Proposed |

**所有生成物均为静态配置文件（YAML、JSON、markdown），不生成运行时 Python 代码。**

## 5. Naming Rules 命名规则

```python
# 必须匹配
PATTERN = r"^[a-z][a-z0-9_]*$"   # snake_case only
MAX_LENGTH = 64                   # 最大长度

# 必须拒绝
- 包含业务词（使用 check_business_terms.py 的禁止列表）
- 覆盖已有模块/模板（除非 --force）
- 包含连字符、空格、大写字母
- 包含 .env、secret、key、password、credential
```

## 6. Dry-Run / Preview / Overwrite Rules

| Mode | Flag | Behavior |
|---|---|---|
| Dry-run | `--dry-run` | 列出将创建的文件，不实际写入 |
| Normal（默认） | — | 创建文件，目标存在时拒绝 |
| Force | `--force` | 覆盖已存在的目标（需显式 opt-in） |

**V0.9.0 明确**：
- `--dry-run` 和 `--force` 尚未实现（V0.9.1 计划实现）
- 当前 `scaffold_module.py` 已实现 Normal 模式（拒绝覆盖）

## 7. Runtime Boundary 运行时边界

| Scaffold 涉及 | Scaffold 不涉及 |
|---|---|
| `modules/<name>/` — 配置文件 + stub | `apps/api/app/` — 运行时代码 |
| `templates/<name>/` — agent 配置 | RunStore、ToolExecutionPipeline |
| `evals/cases/` — eval case stub | Provider、RAG、Workflow、Policy runtime |
| 中性 YAML / JSON / markdown 文件 | 任何 `.py` 运行时文件 |
| 文件系统操作 | 数据库、网络、API 调用 |

**关键原则**：Scaffold 只生成骨架，不改变任何运行时行为。
生成的配置文件需要使用者的 agent 主动引用后才能生效。

## 8. Security Rules 安全规则

- ❌ 不得生成 `.env`、密钥、凭据
- ❌ 不得覆盖已有文件（除非 `--force`）
- ❌ 不得生成业务专用代码
- ✅ 必须校验名称是否包含业务词
- ✅ 必须支持 dry-run preview
- ✅ 生成后建议 `git add <paths>` 提示

## 9. V0.9 Roadmap 路线图

| Version | Scope | 代码改动 |
|---|---|---|
| **V0.9.0** | CLI / Scaffold Contract 文档 | ❌ 无代码改动 |
| V0.9.1 | Enhance scaffold_module.py — dry-run, force, preview | ✅ 改 cli/scaffold_module.py |
| V0.9.2 | Scaffold agent template — generate agent.json | ✅ 改 scripts/ |
| V0.9.3 | Scaffold eval cases — generate eval stubs | ✅ 改 scripts/ |
| V0.9.4 | Scaffold docs / README generator | ✅ 改 scripts/ |
| V0.9.5 | CLI validation and hygiene | ✅ 改 cli/ |
| V0.9.6 | CLI docs consolidation | ❌ 仅文档 |

## 10. Anti-Goals 明确不做的

- ❌ V0.9.0 不实现任何 CLI 代码
- ❌ V0.9.0 不修改 `apps/api/app/`
- ❌ V0.9.0 不修改 `apps/api/tests/`
- ❌ V0.9.0 不修改运行时模块
- ❌ V0.9.0 不新增 API endpoint
- ❌ V0.9.0 不生成业务代码
- ❌ Level 3 CLI（`agent-harness` 命令）当前不承诺

## 11. 相关文档

- [Scaffold Module Test](..)（`apps/api/tests/test_scaffold_module.py`）
- [Agent Template Contract](agent-template-contract.md)
- [Module Development](module-development.md)
