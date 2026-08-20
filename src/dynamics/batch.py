from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import uuid4

from .client import DataverseClient


@dataclass(frozen=True)
class BatchRequest:
    path: str
    content_id: str


class DataverseBatch:
    def __init__(self, client: DataverseClient) -> None:
        self.client = client

    def execute(self, requests: list[BatchRequest]) -> dict[str, int]:
        if not requests:
            return {}

        boundary = f"batch_{uuid4().hex}"
        body = self._build_body(boundary, requests)
        response = self.client.session.post(
            f"{self.client.base_url}/$batch",
            headers={
                "Authorization": f"Bearer {self.client.auth.get_access_token()}",
                "Content-Type": f"multipart/mixed; boundary={boundary}",
            },
            data=body,
            timeout=self.client.timeout,
        )
        response.raise_for_status()
        return self._parse_statuses(response.text)

    def _build_body(self, boundary: str, requests: list[BatchRequest]) -> str:
        parts: list[str] = []
        for item in requests:
            parts.extend([
                f"--{boundary}",
                "Content-Type: application/http",
                "Content-Transfer-Encoding: binary",
                f"Content-ID: {item.content_id}",
                "",
                f"GET {self.client.base_url}/{item.path.lstrip('/')} HTTP/1.1",
                "Accept: application/json",
                "",
            ])
        parts.extend([f"--{boundary}--", ""])
        return "\r\n".join(parts)

    @staticmethod
    def _parse_statuses(body: str) -> dict[str, int]:
        statuses: dict[str, int] = {}
        blocks = re.split(r"(?=Content-ID:\s*)", body, flags=re.IGNORECASE)
        for block in blocks:
            content_id = re.search(r"Content-ID:\s*([^\r\n]+)", block, re.IGNORECASE)
            status = re.search(r"HTTP/1\.1\s+(\d{3})", block)
            if content_id and status:
                statuses[content_id.group(1).strip()] = int(status.group(1))
        return statuses
