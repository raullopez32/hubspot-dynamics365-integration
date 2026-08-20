from __future__ import annotations

from dataclasses import dataclass

from src.dynamics.client import DataverseClient


@dataclass(frozen=True)
class ContactRecord:
    source_id: str
    firstname: str | None
    lastname: str | None
    email: str | None
    mobilephone: str | None


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return normalized or None


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return digits or None


def from_hubspot(contact: dict) -> ContactRecord:
    properties = contact.get("properties", {})
    return ContactRecord(
        source_id=str(contact["id"]),
        firstname=properties.get("firstname") or None,
        lastname=properties.get("lastname") or None,
        email=normalize_email(properties.get("email")),
        mobilephone=normalize_phone(properties.get("mobilephone")),
    )


def to_dataverse_payload(contact: ContactRecord) -> dict:
    payload = {
        "firstname": contact.firstname,
        "lastname": contact.lastname,
        "emailaddress1": contact.email,
        "mobilephone": contact.mobilephone,
    }
    return {key: value for key, value in payload.items() if value is not None}


class ContactSync:
    def __init__(self, client: DataverseClient) -> None:
        self.client = client

    def find_matches(self, contact: ContactRecord) -> list[dict]:
        if contact.email:
            matches = self._search("emailaddress1", contact.email)
            if matches:
                return matches

        if contact.mobilephone:
            return self._search("mobilephone", contact.mobilephone)

        return []

    def sync(self, contact: ContactRecord) -> dict:
        matches = self.find_matches(contact)

        if len(matches) > 1:
            return {
                "source_id": contact.source_id,
                "status": "conflict",
                "matches": [item.get("contactid") for item in matches],
            }

        payload = to_dataverse_payload(contact)

        if matches:
            contact_id = matches[0]["contactid"]
            self.client.request("PATCH", f"contacts({contact_id})", json=payload)
            return {
                "source_id": contact.source_id,
                "status": "updated",
                "target_id": contact_id,
            }

        if not contact.email and not contact.mobilephone:
            return {"source_id": contact.source_id, "status": "skipped"}

        created = self.client.request(
            "POST",
            "contacts",
            json=payload,
            headers={"Prefer": "return=representation"},
        )
        return {
            "source_id": contact.source_id,
            "status": "created",
            "target_id": created.get("contactid"),
        }

    def _search(self, field: str, value: str) -> list[dict]:
        escaped = value.replace("'", "''")
        data = self.client.request(
            "GET",
            "contacts",
            params={
                "$select": "contactid,emailaddress1,mobilephone",
                "$filter": f"{field} eq '{escaped}'",
                "$top": 2,
            },
        )
        return data.get("value", [])
