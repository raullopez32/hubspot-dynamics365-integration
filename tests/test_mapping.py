import json

from src.mapping.loader import MappingConfig
from src.mapping.mapper import PropertyMapper


def test_mapping_loads_entity(tmp_path):
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps({"entities": {"opportunity": {"fields": []}}}))

    config = MappingConfig.load(path)

    assert config.entity("opportunity") == {"fields": []}


def test_mapper_maps_fields_and_reports_required_values():
    mapper = PropertyMapper({
        "fields": [
            {"source": "name", "target": "name", "required": True},
            {"source": "program", "target": "demo_programcode", "required": True},
            {"source": "note", "target": "description"},
        ]
    })

    properties = {"name": "Application", "program": "CS", "note": "Imported"}

    assert mapper.map(properties) == {
        "name": "Application",
        "demo_programcode": "CS",
        "description": "Imported",
    }
    assert mapper.missing_required(properties) == []
    assert mapper.missing_required({"name": "Application"}) == ["program"]
