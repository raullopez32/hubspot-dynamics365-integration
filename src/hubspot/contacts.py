from __future__ import annotations

from .client import HubSpotClient


class HubSpotContacts:
    def __init__(self, client: HubSpotClient, api_version: str = "2026-03") -> None:
        self.client = client
        self.api_version = api_version

    def list_members(self, list_id: str) -> list[str]:
        if not list_id:
            raise ValueError("HubSpot list ID is required")

        members: list[str] = []
        after: str | None = None

        while True:
            params = {"limit": 100}
            if after:
                params["after"] = after

            data = self.client.request(
                "GET",
                f"crm/lists/{self.api_version}/{list_id}/memberships",
                params=params,
            )
            members.extend(str(item["recordId"]) for item in data.get("results", []))

            after = data.get("paging", {}).get("next", {}).get("after")
            if not after:
                return members

    def read(self, contact_ids: list[str], properties: list[str]) -> list[dict]:
        contacts: list[dict] = []

        for offset in range(0, len(contact_ids), 100):
            batch = contact_ids[offset : offset + 100]
            data = self.client.request(
                "POST",
                f"crm/objects/{self.api_version}/contacts/batch/read",
                json={
                    "properties": properties,
                    "inputs": [{"id": contact_id} for contact_id in batch],
                },
            )
            contacts.extend(data.get("results", []))

        return contacts
