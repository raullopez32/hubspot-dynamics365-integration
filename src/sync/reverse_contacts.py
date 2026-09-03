from __future__ import annotations

from dataclasses import dataclass

from src.dynamics.client import DataverseClient
from src.hubspot.contacts import HubSpotContacts

from .contacts import normalize_email, normalize_phone


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

    def read_changed(self, since: str, until: str) -> list[ReverseContact]:
        filters = [f"modifiedon gt {since}", f"modifiedon le {until}"]
        if self.integration_user_id:
            filters.append(f"_modifiedby_value ne {self.integration_user_id}")

        params = {
            "$select": "contactid,firstname,lastname,emailaddress1,mobilephone,modifiedon,_modifiedby_value",
            "$filter": " and ".join(filters),
            "$orderby": "modifiedon asc",
        }
        contacts: list[ReverseContact] = []
        path = "contacts"

        while path:
            data = self.dynamics.request("GET", path, params=params if path == "contacts" else None)
            contacts.extend(
                ReverseContact(
                    source_id=item["contactid"],
                    firstname=item.get("firstname"),
                    lastname=item.get("lastname"),
                    email=normalize_email(item.get("emailaddress1")),
                    mobilephone=normalize_phone(item.get("mobilephone")),
                    modified_on=item["modifiedon"],
                )
                for item in data.get("value", [])
            )
            path = data.get("@odata.nextLink")

        return contacts

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

        target = matches[0]
        current = target.get("properties", {})
        properties = {
            "firstname": contact.firstname,
            "lastname": contact.lastname,
            "email": contact.email,
            "mobilephone": contact.mobilephone,
        }
        properties = {key: value for key, value in properties.items() if value not in (None, "")}

        unchanged = all(
            normalize_email(current.get(key)) == normalize_email(value)
            if key == "email"
            else normalize_phone(current.get(key)) == normalize_phone(value)
            if key == "mobilephone"
            else current.get(key) == value
            for key, value in properties.items()
        )
        target_id = str(target["id"])
        if unchanged:
            return {
                "source_id": contact.source_id,
                "status": "unchanged",
                "target_id": target_id,
                "modified_on": contact.modified_on,
            }

        self.hubspot.update(target_id, properties)
        return {
            "source_id": contact.source_id,
            "status": "updated",
            "target_id": target_id,
            "modified_on": contact.modified_on,
        }
