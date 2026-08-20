from __future__ import annotations


class PropertyMapper:
    def __init__(self, config: dict) -> None:
        self.fields = config.get("fields", [])

    @property
    def source_properties(self) -> list[str]:
        return [field["source"] for field in self.fields]

    def map(self, properties: dict) -> dict:
        mapped = {}
        for field in self.fields:
            value = properties.get(field["source"])
            if value not in (None, ""):
                mapped[field["target"]] = value
        return mapped

    def missing_required(self, properties: dict) -> list[str]:
        return [
            field["source"]
            for field in self.fields
            if field.get("required") and properties.get(field["source"]) in (None, "")
        ]
