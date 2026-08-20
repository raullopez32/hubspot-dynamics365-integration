from __future__ import annotations

import msal


class DataverseAuth:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        base_url: str,
    ) -> None:
        missing = [
            name
            for name, value in {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "client_secret": client_secret,
                "base_url": base_url,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing Dataverse auth settings: {', '.join(missing)}")

        self.base_url = base_url.rstrip("/")
        self.client = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )

    def get_access_token(self) -> str:
        result = self.client.acquire_token_for_client(
            scopes=[f"{self.base_url}/.default"]
        )
        token = result.get("access_token")
        if token:
            return token

        message = result.get("error_description") or result.get("error") or "Unknown authentication error"
        raise RuntimeError(f"Dataverse authentication failed: {message}")
