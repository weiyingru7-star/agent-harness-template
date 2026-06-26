from fastapi.testclient import TestClient

from app.ai_runtime.structured_output import parse_structured_output
from app.main import app


client = TestClient(app)


def test_mock_llm_smoke() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "hello"})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"] == "Mock LLM response for: hello"
    assert data["structured_output"] is None
    assert data["model"] == "mock"
    assert data["latency_ms"] is not None
    assert data["latency_ms"] >= 0
    assert "prompt_tokens" in data["usage"]
    assert "completion_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]
    assert data["finish_reason"] == "stop"
    assert data["metadata"]["contract"] == "ProviderResponse"
    assert data["metadata"]["provider_runtime_version"] == "v0.5.1"
    assert data["metadata"]["mock"] is True


def test_mock_llm_structured_smoke() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "structured": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["structured_output"] == {
        "ok": True,
        "provider": "mock",
        "echo": "hello",
    }
    assert body["model"] == "mock"
    assert body["latency_ms"] is not None
    assert "total_tokens" in body["usage"]
    assert body["finish_reason"] == "stop"
    assert body["metadata"]["mock"] is True


def test_unconfigured_openai_compatible_smoke_fallback_to_mock() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "openai_compatible"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"].startswith("Mock LLM response")
    assert data["metadata"]["fallback_used"] is True
    assert data["metadata"]["fallback_from"] == "openai_compatible"
    assert data["metadata"]["primary_error_type"] == "ProviderConfigurationError"


def test_unknown_provider_smoke_fallback_to_mock() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "unknown"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"].startswith("Mock LLM response")
    assert data["metadata"]["fallback_used"] is True
    assert data["metadata"]["fallback_from"] == "unknown"
    assert data["metadata"]["primary_error_type"] == "ValueError"


def test_parse_structured_output_rejects_non_json() -> None:
    assert parse_structured_output("not json") is None


def test_smoke_response_has_all_provider_response_fields() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "contract check"})

    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "output" in data
    assert "structured_output" in data
    assert "model" in data
    assert "latency_ms" in data
    assert "usage" in data
    assert "finish_reason" in data
    assert "metadata" in data


def test_stream_endpoint_returns_200() -> None:
    response = client.post("/api/llm/stream", json={"prompt": "hello"})

    assert response.status_code == 200


def test_stream_content_type_is_event_stream() -> None:
    response = client.post("/api/llm/stream", json={"prompt": "hello"})

    ct = response.headers.get("content-type", "")
    assert "text/event-stream" in ct


def test_stream_first_event_is_stream_start() -> None:
    events = _parse_stream_response(client, {"prompt": "hello"})

    assert events[0]["event_type"] == "stream_start"
    assert events[0]["index"] == 0


def test_stream_has_delta_events() -> None:
    events = _parse_stream_response(client, {"prompt": "hello"})

    deltas = [e for e in events if e["event_type"] == "stream_delta"]
    assert len(deltas) >= 1


def test_stream_last_event_is_stream_end() -> None:
    events = _parse_stream_response(client, {"prompt": "hello"})

    assert events[-1]["event_type"] == "stream_end"


def test_stream_delta_order_match_full_output() -> None:
    events = _parse_stream_response(client, {"prompt": "hello"})

    deltas = [e["delta"] for e in events if e["event_type"] == "stream_delta"]
    combined = "".join(deltas)
    assert combined == "Mock LLM response for: hello"


def test_stream_index_continuous() -> None:
    events = _parse_stream_response(client, {"prompt": "test"})

    for i, event in enumerate(events):
        assert event["index"] == i


def test_stream_event_has_provider_and_model() -> None:
    events = _parse_stream_response(client, {"prompt": "hello", "provider": "mock"})

    for event in events:
        assert event["provider"] == "mock"
        assert event["model"] == "mock"


def _parse_stream_response(test_client, body: dict) -> list[dict]:
    import json

    resp = test_client.post("/api/llm/stream", json=body)
    result = []
    for line in resp.text.strip().split("\n\n"):
        if line.startswith("data: "):
            result.append(json.loads(line[6:]))
    return result


def test_mock_failing_smoke_fallback_to_mock() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "mock_failing"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"].startswith("Mock LLM response")
    assert data["metadata"]["fallback_used"] is True
    assert data["metadata"]["fallback_from"] == "mock_failing"
    assert data["metadata"]["fallback_to"] == "mock"
    assert data["metadata"]["primary_error_type"] == "ProviderRequestError"


def test_smoke_fallback_success() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "mock_failing", "fallback": "mock"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"].startswith("Mock LLM response")
    assert data["metadata"]["fallback_used"] is True
    assert data["metadata"]["fallback_from"] == "mock_failing"
    assert data["metadata"]["primary_error_type"] == "ProviderRequestError"


def test_smoke_no_fallback_unchanged() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert "fallback_used" not in data["metadata"]


def test_smoke_fallback_unknown_primary() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "unknown", "fallback": "mock"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["metadata"]["fallback_from"] == "unknown"
    assert data["metadata"]["primary_error_type"] == "ValueError"


def test_smoke_mock_flaky_auto_retry() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "mock_flaky", "max_attempts": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock_flaky"
    assert data["output"].startswith("Mock LLM flaky response")
    assert data["metadata"]["retried"] is True
    assert data["metadata"]["retry_count"] == 1


def test_smoke_mock_flaky_retry_metadata() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "mock_flaky", "max_attempts": 2},
    )
    assert response.status_code == 200
    meta = response.json()["metadata"]
    assert "attempts" in meta
    assert meta["max_attempts"] == 2
    assert meta["final_attempt_status"] == "completed"
    assert len(meta["attempts"]) == 2


def test_config_endpoint_returns_200() -> None:
    response = client.get("/api/llm/config")
    assert response.status_code == 200


def test_config_endpoint_fields() -> None:
    response = client.get("/api/llm/config")
    data = response.json()
    assert "provider_name" in data
    assert "model" in data
    assert "timeout_ms" in data
    assert "max_attempts" in data
    assert "fallback_provider" in data
    assert "api_key_configured" in data
    assert data["provider_name"] == "mock"
    assert data["max_attempts"] == 1
    assert data["streaming_enabled"] is True


def test_config_endpoint_key_not_exposed() -> None:
    response = client.get("/api/llm/config")
    data = response.json()
    assert "api_key" not in data
    assert "AI_API_KEY" not in str(data)


def test_smoke_metadata_includes_config_info() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "hello"})
    assert response.status_code == 200
    meta = response.json()["metadata"]
    assert meta["configured_provider"] == "mock"
    assert meta["configured_model"] == "gpt-4o-mini"
    assert meta["config_source"] == "env"