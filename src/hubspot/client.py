from __future__ import annotations

from typing import Any

import requests

from src.http_client import build_retry_session


class HubSpotClient:
    def __init__(
        self,
        access_token: str,
        base_url: str = "https://api.hubapi.com",
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if not access_token:
            raise ValueError("HubSpot access token is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or build_retry_session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.session.request(
            method,
            f"{self.base_url}/{path.lstrip('/')}",
            timeout=kwargs.pop("timeout", self.timeout),
            **kwargs,
        )
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()
