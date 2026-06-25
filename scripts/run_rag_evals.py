#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import gettempdir
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
RAG_CASE_DIR = ROOT / "evals" / "rag_cases"
TEST_ROOT = Path(gettempdir()) / "agent_harness_template_rag_evals"
TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_ROOT / 'eval_rag.db'}"
os.environ["LOCAL_STORAGE_DIR"] = str(TEST_ROOT / "uploads")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from core.db import reset_db  # noqa: E402


REQUIRED_FIELDS = ["id", "name", "documents", "queries"]


@dataclass
class RagEvalResult:
    case_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)


def load_cases(case_paths: list[Path] | None = None) -> list[dict[str, Any]]:
    paths = case_paths or sorted(RAG_CASE_DIR.glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def validate_case(case: dict[str, Any]) -> list[str]:
    failures = [f"missing field: {field}" for field in REQUIRED_FIELDS if field not in case]
    if not isinstance(case.get("documents"), list) or not case["documents"]:
        failures.append("documents must be a non-empty list")
    if not isinstance(case.get("queries"), list) or not case["queries"]:
        failures.append("queries must be a non-empty list")
    return failures


def run_rag_eval_case(case: dict[str, Any], client: TestClient | None = None) -> RagEvalResult:
    case_id = str(case.get("id", "unknown"))
    failures = validate_case(case)
    if failures:
        return RagEvalResult(case_id=case_id, passed=False, failures=failures)

    test_client = client or TestClient(app)

    # Create test documents
    for doc in case["documents"]:
        doc_resp = test_client.post(
            "/api/knowledge/documents",
            json={
                "title": doc["title"],
                "text": doc["text"],
                "source": doc.get("source", "eval"),
            },
        )
        if doc_resp.status_code != 201:
            failures.append(
                f"POST /api/knowledge/documents returned {doc_resp.status_code} for '{doc['title']}'"
            )

    if failures:
        return RagEvalResult(case_id=case_id, passed=False, failures=failures)

    # Run queries and verify
    for q in case["queries"]:
        query_text = q["query"]
        retrieve_resp = test_client.post(
            "/api/knowledge/retrieve",
            json={"query": query_text, "limit": 5},
        )
        if retrieve_resp.status_code != 200:
            failures.append(f"retrieve returned {retrieve_resp.status_code} for query '{query_text}'")
            continue

        results = retrieve_resp.json().get("results", [])

        expected_min = q.get("expected_min_results", 1)
        if len(results) < expected_min:
            failures.append(
                f"query '{query_text}': results {len(results)} < expected_min_results {expected_min}"
            )

        expected_title = q.get("expected_document_title")
        if expected_title and results:
            titles = {r["citation"]["title"] for r in results}
            if expected_title not in titles:
                failures.append(
                    f"query '{query_text}': expected document title '{expected_title}' not in results"
                )

        expected_source = q.get("expected_source")
        if expected_source and results:
            sources = {r["citation"]["source"] for r in results}
            if expected_source not in sources:
                failures.append(
                    f"query '{query_text}': expected source '{expected_source}' not in results"
                )

        expected_text = q.get("expected_chunk_contains")
        if expected_text and results:
            chunk_texts = [r["chunk"]["text"] for r in results]
            if not any(expected_text in t for t in chunk_texts):
                failures.append(
                    f"query '{query_text}': expected text '{expected_text}' not found in any chunk"
                )

        expected_score = q.get("expected_min_score", 1)
        if expected_score and results:
            scores = [r["score"] for r in results]
            if max(scores) < expected_score:
                failures.append(
                    f"query '{query_text}': max score {max(scores)} < expected_min_score {expected_score}"
                )

    return RagEvalResult(case_id=case_id, passed=not failures, failures=failures)


def run_rag_eval_cases(cases: list[dict[str, Any]]) -> list[RagEvalResult]:
    reset_db()
    client = TestClient(app)
    return [run_rag_eval_case(case, client=client) for case in cases]


def main() -> int:
    cases = load_cases()
    if not cases:
        print(f"No RAG eval cases found in {RAG_CASE_DIR}")
        return 1

    results = run_rag_eval_cases(cases)
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.case_id}")
        for failure in result.failures:
            print(f"  - {failure}")

    print(f"Summary: {passed} passed, {failed} failed, {len(results)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
