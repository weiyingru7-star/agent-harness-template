# Changelog 变更记录

所有重要变更都应该记录在这里。

## Entry Template 记录模板

```text
Date:
  YYYY-MM-DD

Stage:
  Stage N - <stage name>

Changed files:
  - <file>

Summary:
  - <what changed>

Validation:
  - <command>: <result>

Notes:
  - <risks, skipped checks, or follow-ups>
```

## 2026-06-24

Stage:
  Stage 1 - Foundation and AI development constraints

Changed files:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `PROJECT_BOUNDARIES.md`
  - `TASK_SPEC.md`
  - `TESTING.md`
  - `CHANGELOG.md`

Summary:
  - 增加 Codex 和 Claude Code 使用的 AI 开发约束。
  - 明确 Stage 1 边界和 Stage 2-5 禁止提前实现的内容。
  - 增加任务规格模板、测试验收说明和变更记录模板。

Validation:
  - 仅文档修改，不需要运行应用测试。

Notes:
  - 未增加 Agent、Run、Step、Event、AI Runtime、RAG、file upload 或 Stage 2-5 目录。
