from __future__ import annotations

import json
from pathlib import Path


class MappingConfig:
    def __init__(self, data: dict) -> None:
        self.data = data

    @classmethod
    def load(cls, path: str | Path) -> "MappingConfig":
        with Path(path).open("r", encoding="utf-8") as file:
            return cls(json.load(file))

    def entity(self, name: str) -> dict:
        try:
            return self.data["entities"][name]
        except KeyError as exc:
            raise ValueError(f"Mapping entity not found: {name}") from exc
