# V1.0 Release Checklist

Run all checks before tagging a new release.

## Tests

```bash
make test-api
```

## Evals

```bash
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py
```

## Template Health

```bash
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
```

## Scaffold Dry-Run

```bash
python3 scripts/scaffold_module.py --name test_check --dry-run
python3 scripts/scaffold_agent.py --name test_check --dry-run
python3 scripts/scaffold_eval.py --name test_check --dry-run
python3 scripts/scaffold_docs.py --name test_check --kind generic --dry-run
```

## Frontend

```bash
cd apps/web && npm run build
```

## Git

```bash
git diff --check
git status
git tag vX.Y.Z
```
