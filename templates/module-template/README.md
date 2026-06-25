# {{module_name}} Module

This module was generated from the generic Agent Harness module template.

## Contents

- `module.yaml`: module metadata
- `agent.yaml`: agent metadata
- `services/{{module_name}}_service.py`: module service with an `execute` entrypoint
- `prompts/system.md`: neutral system prompt
- `skills/`: local module skills
- `evals/`: local module eval assets

Keep module-specific business logic inside this module directory.

## Execution Contract

The module entrypoint is declared in `module.yaml`:

```yaml
entrypoint: modules.{{module_name}}.services.{{module_name}}_service:execute
```

The entrypoint should accept `input_text` and `context`, then return an
`AgentExecutionResult`.
