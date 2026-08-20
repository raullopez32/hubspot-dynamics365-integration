from unittest import mock

from src.sync.opportunities import OpportunitySync


CONFIG = {
    "target_entity": "opportunities",
    "id_field": "opportunityid",
    "contact_bind_field": "customerid_contact@odata.bind",
    "contact_entity": "contacts",
    "key_fields": ["demo_programcode", "demo_periodcode"],
    "fields": [
        {"source": "opportunity_name", "target": "name", "required": True},
        {"source": "program_code", "target": "demo_programcode", "required": True},
        {"source": "period_code", "target": "demo_periodcode", "required": True},
    ],
}


def test_existing_opportunity_is_updated():
    client = mock.Mock()
    client.request.side_effect = [
        {"value": [{"opportunityid": "opp-1"}]},
        {},
    ]
    sync = OpportunitySync(client, CONFIG)

    result = sync.sync(
        "42",
        {
            "opportunity_name": "Application",
            "program_code": "CS",
            "period_code": "2026-FALL",
        },
        "contact-1",
    )

    assert result == {"source_id": "42", "status": "updated", "target_id": "opp-1"}
    client.request.assert_any_call(
        "PATCH",
        "opportunities(opp-1)",
        json={
            "name": "Application",
            "demo_programcode": "CS",
            "demo_periodcode": "2026-FALL",
        },
    )


def test_new_opportunity_is_linked_to_contact():
    client = mock.Mock()
    client.request.side_effect = [
        {"value": []},
        {"opportunityid": "opp-2"},
    ]
    sync = OpportunitySync(client, CONFIG)

    result = sync.sync(
        "42",
        {
            "opportunity_name": "Application",
            "program_code": "CS",
            "period_code": "2026-FALL",
        },
        "contact-1",
    )

    assert result == {"source_id": "42", "status": "created", "target_id": "opp-2"}
    client.request.assert_any_call(
        "POST",
        "opportunities",
        json={
            "name": "Application",
            "demo_programcode": "CS",
            "demo_periodcode": "2026-FALL",
            "customerid_contact@odata.bind": "/contacts(contact-1)",
        },
        headers={"Prefer": "return=representation"},
    )


def test_multiple_matches_return_conflict():
    client = mock.Mock()
    client.request.return_value = {
        "value": [
            {"opportunityid": "opp-1"},
            {"opportunityid": "opp-2"},
        ]
    }
    sync = OpportunitySync(client, CONFIG)

    result = sync.sync(
        "42",
        {
            "opportunity_name": "Application",
            "program_code": "CS",
            "period_code": "2026-FALL",
        },
        "contact-1",
    )

    assert result == {
        "source_id": "42",
        "status": "conflict",
        "matches": ["opp-1", "opp-2"],
    }


def test_missing_required_property_is_invalid():
    client = mock.Mock()
    sync = OpportunitySync(client, CONFIG)

    result = sync.sync("42", {"opportunity_name": "Application"}, "contact-1")

    assert result == {
        "source_id": "42",
        "status": "invalid",
        "missing": ["program_code", "period_code"],
    }
    client.request.assert_not_called()
