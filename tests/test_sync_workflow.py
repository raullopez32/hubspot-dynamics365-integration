from unittest import mock

from src.sync.workflow import SyncWorkflow


OPPORTUNITY_CONFIG = {
    "fields": [
        {"source": "opportunity_name", "target": "name", "required": True},
        {"source": "program_code", "target": "demo_programcode", "required": True},
    ]
}


def test_workflow_syncs_opportunity_after_contact():
    hubspot = mock.Mock()
    hubspot.list_members.return_value = ["1"]
    hubspot.read.return_value = [
        {
            "id": "1",
            "properties": {
                "firstname": "Raul",
                "lastname": "Lopez",
                "email": "raul@example.com",
                "mobilephone": None,
                "opportunity_name": "Application",
                "program_code": "CS",
            },
        }
    ]

    contacts = mock.Mock()
    contacts.sync.return_value = {
        "source_id": "1",
        "status": "updated",
        "target_id": "contact-1",
    }

    opportunities = mock.Mock()
    opportunities.config = OPPORTUNITY_CONFIG
    opportunities.sync.return_value = {
        "source_id": "1",
        "status": "created",
        "target_id": "opp-1",
    }

    workflow = SyncWorkflow(hubspot, contacts, opportunities)
    result = workflow.run("123")

    assert result == {
        "contacts": {"updated": 1},
        "opportunities": {"created": 1},
        "processed": 1,
    }
    hubspot.read.assert_called_once_with(
        ["1"],
        [
            "firstname",
            "lastname",
            "email",
            "mobilephone",
            "opportunity_name",
            "program_code",
        ],
    )
    opportunities.sync.assert_called_once_with(
        "1",
        hubspot.read.return_value[0]["properties"],
        "contact-1",
    )


def test_workflow_skips_opportunity_when_contact_has_no_target():
    hubspot = mock.Mock()
    hubspot.list_members.return_value = ["1"]
    hubspot.read.return_value = [
        {
            "id": "1",
            "properties": {
                "email": "duplicate@example.com",
                "opportunity_name": "Application",
                "program_code": "CS",
            },
        }
    ]

    contacts = mock.Mock()
    contacts.sync.return_value = {
        "source_id": "1",
        "status": "conflict",
        "matches": ["a", "b"],
    }

    opportunities = mock.Mock()
    opportunities.config = OPPORTUNITY_CONFIG

    workflow = SyncWorkflow(hubspot, contacts, opportunities)
    result = workflow.run("123")

    assert result == {
        "contacts": {"conflict": 1},
        "opportunities": {},
        "processed": 1,
    }
    opportunities.sync.assert_not_called()


def test_workflow_returns_empty_summary_for_empty_list():
    hubspot = mock.Mock()
    hubspot.list_members.return_value = []
    opportunities = mock.Mock()
    opportunities.config = OPPORTUNITY_CONFIG

    workflow = SyncWorkflow(hubspot, mock.Mock(), opportunities)

    assert workflow.run("123") == {
        "contacts": {},
        "opportunities": {},
        "processed": 0,
    }
