from __future__ import annotations

from dataclasses import dataclass

from src.dynamics.client import DataverseClient
from src.hubspot.contacts import HubSpotContacts

from .contacts import normalize_email


@dataclass(frozen=True)
class ReverseContact:
    source_id: str
    firstname: str | None
    lastname: str | None
    email: str | None
    mobilephone: str | None
    modified_on: str


class ReverseContactSync:
    def __init__(
        self,
        dynamics: DataverseClient,
        hubspot: HubSpotContacts,
        integration_user_id: str | None = None,
    ) -> None:
        self.dynamics = dynamics
        self.hubspot = hubspot
        self.integration_user_id = integration_user_id

    def read_changed(self, since: str) -> list[ReverseContact]:
        filters = [f"modifiedon gt {since}"]
        if self.integration_user_id:
            filters.append(f"_modifiedby_value ne {self.integration_user_id}")

        data = self.dynamics.request(
            "GET",
            "contacts",
            params={
                "$select": "contactid,firstname,lastname,emailaddress1,mobilephone,modifiedon,_modifiedby_value",
                "$filter": " and ".join(filters),
                "$orderby": "modifiedon asc",
            },
        )

        return [
            ReverseContact(
                source_id=item["contactid"],
                firstname=item.get("firstname"),
                lastname=item.get("lastname"),
                email=normalize_email(item.get("emailaddress1")),
                mobilephone=item.get("mobilephone"),
                modified_on=item["modifiedon"],
            )
            for item in data.get("value", [])
        ]

    def sync(self, contact: ReverseContact) -> dict:
        if not contact.email:
            return {"source_id": contact.source_id, "status": "skipped"}

        matches = self.hubspot.search_by_email(contact.email)
        if len(matches) > 1:
            return {
                "source_id": contact.source_id,
                "status": "conflict",
                "matches": [item.get("id") for item in matches],
            }
        if not matches:
            return {"source_id": contact.source_id, "status": "missing"}

        properties = {
            "firstname": contact.firstname,
            "lastname": contact.lastname,
            "email": contact.email,
            "phone": contact.mobilephone,
        }
        properties = {key: value for key, value in properties.items() if value not in (None, "")}
        target_id = str(matches[0]["id"])
        self.hubspot.update(target_id, properties)

        return {
            "source_id": contact.source_id,
            "status": "updated",
            "target_id": target_id,
            "modified_on": contact.modified_on,
        }
