from unittest import mock

from src.app import create_app


def test_health():
    client = create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_sync_returns_workflow_summary(monkeypatch):
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "token")
    monkeypatch.setenv("HUBSPOT_LIST_ID", "123")
    monkeypatch.setenv("DYNAMICS_TENANT_ID", "tenant")
    monkeypatch.setenv("DYNAMICS_CLIENT_ID", "client")
    monkeypatch.setenv("DYNAMICS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("DYNAMICS_BASE_URL", "https://example.crm.dynamics.com")

    workflow = mock.Mock()
    workflow.run.return_value = {
        "processed": 2,
        "contacts": {"updated": 2},
        "opportunities": {"created": 1, "updated": 1},
    }
    builder = mock.Mock(return_value=workflow)

    client = create_app(builder).test_client()
    response = client.post("/sync")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "processed": 2,
        "contacts": {"updated": 2},
        "opportunities": {"created": 1, "updated": 1},
    }
    workflow.run.assert_called_once_with("123")


def test_sync_rejects_missing_configuration(monkeypatch):
    for name in [
        "HUBSPOT_ACCESS_TOKEN",
        "HUBSPOT_LIST_ID",
        "DYNAMICS_TENANT_ID",
        "DYNAMICS_CLIENT_ID",
        "DYNAMICS_CLIENT_SECRET",
        "DYNAMICS_BASE_URL",
    ]:
        monkeypatch.delenv(name, raising=False)

    client = create_app().test_client()
    response = client.post("/sync")

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_sync_hides_internal_errors(monkeypatch):
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "token")
    monkeypatch.setenv("HUBSPOT_LIST_ID", "123")
    monkeypatch.setenv("DYNAMICS_TENANT_ID", "tenant")
    monkeypatch.setenv("DYNAMICS_CLIENT_ID", "client")
    monkeypatch.setenv("DYNAMICS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("DYNAMICS_BASE_URL", "https://example.crm.dynamics.com")

    builder = mock.Mock(side_effect=RuntimeError("private upstream error"))
    client = create_app(builder).test_client()
    response = client.post("/sync")

    assert response.status_code == 500
    assert response.get_json() == {
        "status": "error",
        "error": "Synchronization failed",
    }
