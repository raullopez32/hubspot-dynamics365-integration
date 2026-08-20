from __future__ import annotations

from src.hubspot.contacts import HubSpotContacts

from .contacts import ContactSync, from_hubspot


class ContactSyncService:
    properties = ["firstname", "lastname", "email", "mobilephone"]

    def __init__(self, hubspot: HubSpotContacts, contacts: ContactSync) -> None:
        self.hubspot = hubspot
        self.contacts = contacts

    def run(self, list_id: str) -> list[dict]:
        contact_ids = self.hubspot.list_members(list_id)
        if not contact_ids:
            return []

        source_contacts = self.hubspot.read(contact_ids, self.properties)
        return [self.contacts.sync(from_hubspot(contact)) for contact in source_contacts]
