# Task Specification Template 任务规格模板

每次开发任务开始前，都应该先使用本文档中的标准格式确认范围。

## Standard Task Format 标准任务格式

```text
Task:
  <short task name>

Stage:
  <current approved stage>

Goal:
  <what should be true after this task>

Allowed files:
  - <file or directory>

Forbidden files:
  - <file or directory>

Allowed behavior:
  - <specific behavior to add or change>

Forbidden behavior:
  - <behavior that must not be added>

Acceptance criteria:
  - <observable outcome>

Test commands:
  - <command>

Rollback:
  - <how to revert if needed>
```

## Required Fields 必填字段

### Task Goal 任务目标

描述这个任务完成后最小且可验证的结果。目标必须足够具体，不能依赖猜测。

### Allowed Files 允许修改文件

列出所有允许修改的文件或目录。

如果实现过程中发现必须修改未列出的文件，先停下来问用户，不要直接改。

### Forbidden Files 禁止修改文件

列出不能修改的文件和目录。

Stage 1 默认禁止以下路径：

- `core`
- `ai_runtime`
- `harness`
- `skills`
- `tools`
- `modules`
- `templates`
- `cli`
- `schemas`
- `evals`

### Acceptance Criteria 验收标准

验收标准必须是可观察、可检查的结果。优先使用这类标准：

- 接口返回预期 JSON
- 页面展示预期状态
- Docker 服务变为 healthy
- 测试命令通过

### Test Commands 测试命令

每个任务都必须写明应该运行的具体命令。

Stage 1 常用命令：

- `make test-api`
- `make up`
- `make dev-api`
- `make dev-web`

### Rollback 回滚方式

回滚方式应该说明改了哪些文件，以及最安全的撤销方式。

示例：

```text
Rollback:
  Revert changes to AGENTS.md and TESTING.md. No generated code or database migration is involved.
```

## Pre-Change Checklist 修改前检查清单

编辑文件前必须确认：

- 当前任务属于当前阶段。
- 所有待修改文件都在允许范围内。
- 已向用户说明计划修改哪些文件。
- 如果范围不清楚，已经先提问。

## Post-Change Checklist 修改后检查清单

编辑文件后必须说明：

- 修改了哪些文件。
- 每个文件改了什么。
- 已运行或建议运行哪些验收命令。
- 哪些命令没有运行。
- 确认没有加入未来阶段功能。
