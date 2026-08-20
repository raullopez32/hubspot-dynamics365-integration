from __future__ import annotations

from src.dynamics.client import DataverseClient
from src.mapping.mapper import PropertyMapper


class OpportunitySync:
    def __init__(self, client: DataverseClient, config: dict) -> None:
        self.client = client
        self.config = config
        self.mapper = PropertyMapper(config)

    def sync(self, source_id: str, properties: dict, contact_id: str) -> dict:
        missing = self.mapper.missing_required(properties)
        if missing:
            return {
                "source_id": source_id,
                "status": "invalid",
                "missing": missing,
            }

        payload = self.mapper.map(properties)
        matches = self.find_matches(contact_id, payload)

        if len(matches) > 1:
            return {
                "source_id": source_id,
                "status": "conflict",
                "matches": [item.get(self.config["id_field"]) for item in matches],
            }

        entity = self.config["target_entity"]
        id_field = self.config["id_field"]

        if matches:
            opportunity_id = matches[0][id_field]
            self.client.request("PATCH", f"{entity}({opportunity_id})", json=payload)
            return {
                "source_id": source_id,
                "status": "updated",
                "target_id": opportunity_id,
            }

        payload[self.config["contact_bind_field"]] = (
            f"/{self.config['contact_entity']}({contact_id})"
        )
        created = self.client.request(
            "POST",
            entity,
            json=payload,
            headers={"Prefer": "return=representation"},
        )
        return {
            "source_id": source_id,
            "status": "created",
            "target_id": created.get(id_field),
        }

    def find_matches(self, contact_id: str, payload: dict) -> list[dict]:
        filters = [f"_customerid_value eq {contact_id}"]
        for field in self.config.get("key_fields", []):
            value = payload.get(field)
            if value is None:
                continue
            escaped = str(value).replace("'", "''")
            filters.append(f"{field} eq '{escaped}'")

        data = self.client.request(
            "GET",
            self.config["target_entity"],
            params={
                "$select": self.config["id_field"],
                "$filter": " and ".join(filters),
                "$top": 2,
            },
        )
        return data.get("value", [])
