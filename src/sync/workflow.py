from __future__ import annotations

from collections import Counter

from src.hubspot.contacts import HubSpotContacts
from src.mapping.mapper import PropertyMapper

from .contacts import ContactSync, from_hubspot
from .opportunities import OpportunitySync


class SyncWorkflow:
    contact_properties = ["firstname", "lastname", "email", "mobilephone"]

    def __init__(
        self,
        hubspot: HubSpotContacts,
        contacts: ContactSync,
        opportunities: OpportunitySync,
    ) -> None:
        self.hubspot = hubspot
        self.contacts = contacts
        self.opportunities = opportunities
        self.opportunity_mapper = PropertyMapper(opportunities.config)

    def run(self, list_id: str) -> dict:
        contact_ids = self.hubspot.list_members(list_id)
        if not contact_ids:
            return {"contacts": {}, "opportunities": {}, "processed": 0}

        properties = list(dict.fromkeys(
            self.contact_properties + self.opportunity_mapper.source_properties
        ))
        source_contacts = self.hubspot.read(contact_ids, properties)

        contact_results = []
        opportunity_results = []

        for source in source_contacts:
            contact_result = self.contacts.sync(from_hubspot(source))
            contact_results.append(contact_result)

            target_id = contact_result.get("target_id")
            if not target_id:
                continue

            opportunity_results.append(
                self.opportunities.sync(
                    str(source["id"]),
                    source.get("properties", {}),
                    target_id,
                )
            )

        return {
            "contacts": self._count(contact_results),
            "opportunities": self._count(opportunity_results),
            "processed": len(source_contacts),
        }

    @staticmethod
    def _count(results: list[dict]) -> dict[str, int]:
        return dict(Counter(result["status"] for result in results))
