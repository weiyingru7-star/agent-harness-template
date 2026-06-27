# CLI / Scaffold Troubleshooting CLI 脚手架故障排查

## Name does not match snake_case 名称不符合 snake_case

```
Error: Module name must use snake_case (lowercase letters, digits, underscores),
starting with a letter. Got: 'BadName'
```

**原因**: 模块/Agent/Eval/Docs 名称只能使用小写字母、数字和下划线，必须以字母开头。

**修复**:
```bash
# 错误
python3 scripts/scaffold_module.py --name MyModule
python3 scripts/scaffold_module.py --name my-module
python3 scripts/scaffold_module.py --name my module
python3 scripts/scaffold_module.py --name 123module

# 正确
python3 scripts/scaffold_module.py --name my_module
python3 scripts/scaffold_module.py --name sample
```

## Target already exists 目标已存在

```
Error: Module already exists at modules/my_module/. Use --force to overwrite.
```

**原因**: 目标目录或文件已经存在。scaffold 默认拒绝覆盖，防止误删已有工作。

**修复**:
```bash
# 确认可以覆盖后
python3 scripts/scaffold_module.py --name my_module --force
```

**注意**: `--force` 只能覆盖 scaffold 管理的目标范围，不会删除项目其他文件。

## Path traversal detected 路径穿越拒绝

```
Error: Path traversal detected in module name: '../x'
```

**原因**: 名称中包含 `..`、`/` 或 `\`，试图访问 scaffold 目标目录之外的位置。

**修复**: 使用简单的 snake_case 名称。

```bash
python3 scripts/scaffold_module.py --name my_module
```

## Sensitive name rejected 敏感名称拒绝

```
Error: Module name 'secret' is reserved and cannot be used.
```

**原因**: 名称是保留的敏感词汇（如 `.env`、`secret`、`key`、`token`、`password` 等），
为防止意外生成包含敏感内容的文件而被拒绝。

**修复**: 使用非敏感名称。

## Business term rejected 业务词拒绝

```
Error: Module name 'ecommerce' contains a business term. Names must be business-neutral.
```

**原因**: 名称中包含业务词（如 `ecommerce`、`order`、`refund` 等）。
agent-harness-template 是通用模板，不能绑定具体行业。

**修复**: 使用中性名称。业务相关代码应放在单独的仓库中。

## Dry-run did not write files Dry-run 没有写文件

**现象**: 运行 `--dry-run` 后输出了文件列表但没有生成实际文件。

**原因**: 这是正常行为。`--dry-run` 只预览将创建的文件，不写入磁盘。

**修复**: 去掉 `--dry-run` 即可正常生成。

```bash
python3 scripts/scaffold_module.py --name my_module
```

## Generated files appear in unexpected locations 生成文件出现在意外位置

**确认生成位置**:

| 命令 | 默认位置 |
|---|---|
| `scaffold_module.py` | `modules/<name>/` |
| `scaffold_agent.py` | `templates/<name>/` |
| `scaffold_eval.py` | `evals/cases/<name>.json` |
| `scaffold_docs.py` | `docs/scaffolds/<kind>-<name>.md` |

如果你在这些位置之外发现了生成文件，可能是 `--name` 参数包含了路径字符（如 `../`）。
这种请求会被 `resolve_safe_target()` 阻止。

## Do not commit sample / demo / test scaffolds 不要提交示例生成物

`--dry-run` 不会写文件，所以不会产生需要提交的内容。

Normal 模式会在 `modules/`、`templates/`、`evals/cases/`、`docs/scaffolds/`
下生成文件。如果这些只是用于测试 scaffold 功能，在提交前请删除它们：

```bash
rm -rf modules/sample_module
rm -rf templates/sample_agent
rm -f evals/cases/sample_eval.json
rm -f docs/scaffolds/*-sample_*.md
```

或者使用 `tmp_path` 隔离的测试来验证 scaffold 功能，不要用真实目录。
