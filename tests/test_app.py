from src.app import create_app


def test_health():
    client = create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_sync_is_not_implemented_yet():
    client = create_app().test_client()
    response = client.post("/sync")

    assert response.status_code == 501
    assert response.get_json() == {"status": "not_implemented"}
