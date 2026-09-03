from unittest import mock

from src.sync.reverse_contacts import ReverseContact, ReverseContactSync


def test_read_changed_excludes_integration_user():
    dynamics = mock.Mock()
    dynamics.request.return_value = {
        "value": [
            {
                "contactid": "contact-1",
                "firstname": "Raul",
                "lastname": "Lopez",
                "emailaddress1": " Raul@example.com ",
                "mobilephone": "+52 81 1234 5678",
                "modifiedon": "2026-08-20T12:00:00Z",
                "_modifiedby_value": "user-1",
            }
        ]
    }
    sync = ReverseContactSync(dynamics, mock.Mock(), "integration-user")

    contacts = sync.read_changed("2026-08-20T11:00:00Z", "2026-08-20T13:00:00Z")

    assert contacts[0].email == "raul@example.com"
    assert contacts[0].mobilephone == "528112345678"
    dynamics.request.assert_called_once_with(
        "GET",
        "contacts",
        params={
            "$select": "contactid,firstname,lastname,emailaddress1,mobilephone,modifiedon,_modifiedby_value",
            "$filter": (
                "modifiedon gt 2026-08-20T11:00:00Z and modifiedon le 2026-08-20T13:00:00Z "
                "and _modifiedby_value ne integration-user"
            ),
            "$orderby": "modifiedon asc",
        },
    )


def test_read_changed_follows_next_link():
    dynamics = mock.Mock()
    dynamics.request.side_effect = [
        {
            "value": [],
            "@odata.nextLink": "https://example.crm.dynamics.com/api/data/v9.2/contacts?$skiptoken=abc",
        },
        {"value": []},
    ]
    sync = ReverseContactSync(dynamics, mock.Mock())

    assert sync.read_changed("2026-08-20T11:00:00Z", "2026-08-20T13:00:00Z") == []
    assert dynamics.request.call_count == 2
    dynamics.request.assert_called_with(
        "GET",
        "https://example.crm.dynamics.com/api/data/v9.2/contacts?$skiptoken=abc",
        params=None,
    )


def test_existing_hubspot_contact_is_updated():
    hubspot = mock.Mock()
    hubspot.search_by_email.return_value = [{"id": "hs-1", "properties": {}}]
    sync = ReverseContactSync(mock.Mock(), hubspot)
    contact = ReverseContact(
        source_id="contact-1",
        firstname="Raul",
        lastname="Lopez",
        email="raul@example.com",
        mobilephone="528112345678",
        modified_on="2026-08-20T12:00:00Z",
    )

    result = sync.sync(contact)

    assert result["status"] == "updated"
    hubspot.update.assert_called_once_with(
        "hs-1",
        {
            "firstname": "Raul",
            "lastname": "Lopez",
            "email": "raul@example.com",
            "mobilephone": "528112345678",
        },
    )


def test_unchanged_hubspot_contact_is_not_written():
    hubspot = mock.Mock()
    hubspot.search_by_email.return_value = [{
        "id": "hs-1",
        "properties": {
            "firstname": "Raul",
            "lastname": "Lopez",
            "email": "RAUL@example.com",
            "mobilephone": "+52 81 1234 5678",
        },
    }]
    sync = ReverseContactSync(mock.Mock(), hubspot)
    contact = ReverseContact(
        "contact-1", "Raul", "Lopez", "raul@example.com", "528112345678", "2026-08-20T12:00:00Z"
    )

    result = sync.sync(contact)

    assert result["status"] == "unchanged"
    hubspot.update.assert_not_called()


def test_missing_hubspot_contact_is_not_created():
    hubspot = mock.Mock()
    hubspot.search_by_email.return_value = []
    sync = ReverseContactSync(mock.Mock(), hubspot)
    contact = ReverseContact(
        "contact-1", "Raul", "Lopez", "raul@example.com", None, "2026-08-20T12:00:00Z"
    )

    assert sync.sync(contact) == {"source_id": "contact-1", "status": "missing"}
    hubspot.update.assert_not_called()


def test_multiple_hubspot_matches_return_conflict():
    hubspot = mock.Mock()
    hubspot.search_by_email.return_value = [{"id": "hs-1"}, {"id": "hs-2"}]
    sync = ReverseContactSync(mock.Mock(), hubspot)
    contact = ReverseContact(
        "contact-1", None, None, "raul@example.com", None, "2026-08-20T12:00:00Z"
    )

    result = sync.sync(contact)

    assert result["status"] == "conflict"
    hubspot.update.assert_not_called()


def test_contact_without_email_is_skipped():
    hubspot = mock.Mock()
    sync = ReverseContactSync(mock.Mock(), hubspot)
    contact = ReverseContact(
        "contact-1", "Raul", "Lopez", None, "528112345678", "2026-08-20T12:00:00Z"
    )

    assert sync.sync(contact) == {"source_id": "contact-1", "status": "skipped"}
    hubspot.search_by_email.assert_not_called()
