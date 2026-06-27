# Using This Template

How to take this Agent Harness Template and build your own agent project.

## When to Fork

Fork this repository when you want to:

- Build a custom agent application on top of this harness
- Add domain-specific modules and agent configurations
- Maintain your own deployment pipeline
- Contribute improvements back to the upstream template

**Keep your fork's `main` branch aligned with upstream.** Use feature branches for your custom work.

## When to Clone and Rename

Clone (then rename the remote) when you want to:

- Experiment with the template structure
- Learn how the harness works
- Create a one-off project that does not need upstream updates

```bash
git clone <repo-url> my-agent-project
cd my-agent-project
git remote rename origin upstream
```

You now own `my-agent-project` with no upstream dependency.

## How to Stay Separated

The template core must remain business-neutral so anyone can reuse it.

| Keep in template core | Keep in your project |
|---|---|
| `modules/<your_module>/` — module config and stubs | Business logic in a separate repo |
| `templates/<your_agent>/` — agent config | Real API keys and credentials |
| `evals/cases/<your_eval>.json` — eval stubs | `.env` file |
| Stub metadata and neutral README | Domain-specific prompts and workflows |

**Rules:**

- Never commit `.env`, secrets, or API keys to any repo
- Never add business terms to `CLAUDE.md`, `AGENTS.md`, or template-level docs
- Never modify `apps/api/app/` runtime code directly for your custom logic — use the scaffold system
- Never change the template scaffold scripts to match your project's naming conventions

## Scaffold Workflow

See [CLI Scaffold Guide](docs/cli-scaffold-guide.md) for full documentation of the four scaffold commands:

```bash
python3 scripts/scaffold_module.py --name <module_name>    # new module skeleton
python3 scripts/scaffold_agent.py --name <agent_name>      # new agent config
python3 scripts/scaffold_eval.py --name <eval_name>        # new eval case
python3 scripts/scaffold_docs.py --name <name> --kind <k>  # new docs stub
```

## Keeping Upstream Changes

If you forked the template, you can pull upstream changes:

```bash
git fetch upstream
git rebase upstream/main
```

If you cloned and renamed, there is no upstream — you own the project.

## Related

- [Quick Start](QUICKSTART.md)
- [CLI Scaffold Troubleshooting](docs/cli-scaffold-troubleshooting.md)
- [Template Release Checklist](docs/template-release-checklist.md)
