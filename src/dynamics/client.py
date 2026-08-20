from __future__ import annotations

from typing import Any

import requests

from .auth import DataverseAuth


class DataverseClient:
    def __init__(
        self,
        auth: DataverseAuth,
        api_version: str = "v9.2",
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.auth = auth
        self.api_version = api_version.strip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        })

    @property
    def base_url(self) -> str:
        return f"{self.auth.base_url}/api/data/{self.api_version}"

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {self.auth.get_access_token()}"

        response = self.session.request(
            method,
            f"{self.base_url}/{path.lstrip('/')}",
            headers=headers,
            timeout=kwargs.pop("timeout", self.timeout),
            **kwargs,
        )
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()
