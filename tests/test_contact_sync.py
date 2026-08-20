from unittest import mock

from src.sync.contacts import ContactRecord, ContactSync, from_hubspot


def test_from_hubspot_normalizes_identity_fields():
    contact = from_hubspot({
        "id": "42",
        "properties": {
            "firstname": "Raul",
            "lastname": "Lopez",
            "email": " Raul@example.com ",
            "mobilephone": "+52 (81) 1234-5678",
        },
    })

    assert contact.email == "raul@example.com"
    assert contact.mobilephone == "528112345678"


def test_existing_contact_is_updated():
    client = mock.Mock()
    client.request.side_effect = [
        {"value": [{"contactid": "abc"}]},
        {},
    ]
    sync = ContactSync(client)

    result = sync.sync(ContactRecord("42", "Raul", "Lopez", "raul@example.com", None))

    assert result["status"] == "updated"
    assert result["target_id"] == "abc"
    client.request.assert_any_call(
        "PATCH",
        "contacts(abc)",
        json={"firstname": "Raul", "lastname": "Lopez", "emailaddress1": "raul@example.com"},
    )


def test_multiple_matches_return_conflict():
    client = mock.Mock()
    client.request.return_value = {
        "value": [{"contactid": "a"}, {"contactid": "b"}],
    }
    sync = ContactSync(client)

    result = sync.sync(ContactRecord("42", None, None, "raul@example.com", None))

    assert result == {
        "source_id": "42",
        "status": "conflict",
        "matches": ["a", "b"],
    }


def test_contact_without_identity_is_skipped():
    client = mock.Mock()
    sync = ContactSync(client)

    result = sync.sync(ContactRecord("42", "Raul", "Lopez", None, None))

    assert result == {"source_id": "42", "status": "skipped"}
    client.request.assert_not_called()
