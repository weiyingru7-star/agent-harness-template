# Example Agent Template

此目录包含业务无关的 example agent template `generic_agent`，
可作为创建新 Agent 的参考起点。

## 文件

- `agent.json`：模板定义文件

## 什么是 Example Agent Template

此目录中的 `generic_agent` **不是业务 Agent**。它只是展示 agent.json
的结构和字段用法。你可以把它作为创建新 Agent 的起点——复制一份、修改
`id`/`name`/`provider`/`tools` 等字段即可创建自己的 Agent 模板。

## 如何查看

保证 API 服务在运行（`make dev-api`）：

```bash
# 列出所有模板
curl http://localhost:8005/api/agent-templates | python3 -m json.tool

# 查看 generic_agent 详情
curl http://localhost:8005/api/agent-templates/generic_agent | python3 -m json.tool

# 查看完整配置
curl http://localhost:8005/api/agent-templates/generic_agent/config | python3 -m json.tool

# 校验模板
curl http://localhost:8005/api/agent-templates/generic_agent/validate
```

## 如何基于此模板创建新 Agent

```bash
# 复制模板目录
cp -r templates/agent-template templates/my_agent

# 修改 agent.json 中的 id/name/provider/tools 等字段
# 重启 API 后通过 API 验证
curl http://localhost:8005/api/agent-templates/my_agent | python3 -m json.tool
```
