from fastapi.testclient import TestClient

from ai_receptionist.app.main import app


client = TestClient(app)


def test_health_status_code():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
