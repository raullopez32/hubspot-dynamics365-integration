from unittest.mock import Mock

from src.hubspot.client import HubSpotClient


def test_hubspot_client_sends_bearer_token_and_returns_json():
    session = Mock()
    response = Mock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = {"results": []}
    session.request.return_value = response

    client = HubSpotClient("token", session=session)
    result = client.request("GET", "/crm/v3/objects/contacts")

    session.headers.update.assert_called_once_with({
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    })
    session.request.assert_called_once_with(
        "GET",
        "https://api.hubapi.com/crm/v3/objects/contacts",
        timeout=30.0,
    )
    response.raise_for_status.assert_called_once()
    assert result == {"results": []}
