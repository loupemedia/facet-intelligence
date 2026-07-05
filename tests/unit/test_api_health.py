"""Test intent: health endpoint returns ok status for load balancers.
Would fail if: router not mounted under /v1/health."""

from fastapi.testclient import TestClient

from facet_intelligence.api.app import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "facet-intelligence"
