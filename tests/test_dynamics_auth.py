from unittest.mock import Mock, patch

from src.dynamics.auth import DataverseAuth


def test_dataverse_auth_uses_client_credentials_scope():
    app = Mock()
    app.acquire_token_for_client.return_value = {"access_token": "token"}

    with patch("src.dynamics.auth.msal.ConfidentialClientApplication", return_value=app) as client_app:
        auth = DataverseAuth(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            base_url="https://example.crm.dynamics.com",
        )

    token = auth.get_access_token()

    client_app.assert_called_once_with(
        client_id="client",
        client_credential="secret",
        authority="https://login.microsoftonline.com/tenant",
    )
    app.acquire_token_for_client.assert_called_once_with(
        scopes=["https://example.crm.dynamics.com/.default"]
    )
    assert token == "token"
