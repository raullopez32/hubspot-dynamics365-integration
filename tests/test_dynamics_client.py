from unittest.mock import Mock

from src.dynamics.client import DataverseClient


def test_dataverse_client_builds_web_api_request():
    auth = Mock()
    auth.base_url = "https://example.crm.dynamics.com"
    auth.get_access_token.return_value = "token"

    session = Mock()
    response = Mock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = {"value": []}
    session.request.return_value = response

    client = DataverseClient(auth, session=session)
    result = client.request("GET", "/contacts?$top=1")

    session.request.assert_called_once_with(
        "GET",
        "https://example.crm.dynamics.com/api/data/v9.2/contacts?$top=1",
        headers={"Authorization": "Bearer token"},
        timeout=30.0,
    )
    response.raise_for_status.assert_called_once()
    assert result == {"value": []}
