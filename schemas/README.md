# schemas

Schema 草案目录预留。

V0.1.1 不引入强制 schema 校验，不改变现有 API 行为。

未来这里可承载模块配置、Agent 配置、Run、Event、File、Artifact 和知识检索结构的 JSON Schema 草案。

## Validation

V0.1.5 增加 schema contract 测试，检查所有 `*.schema.json` 文件都是合法 JSON，并包含核心契约字段。

手动校验：

```bash
for f in schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done
```
