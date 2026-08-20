from unittest import mock

from src.sync.service import ContactSyncService


def test_service_reads_list_contacts_and_syncs_them():
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
            },
        }
    ]
    contacts = mock.Mock()
    contacts.sync.return_value = {
        "source_id": "1",
        "status": "updated",
        "target_id": "abc",
    }

    service = ContactSyncService(hubspot, contacts)
    result = service.run("123")

    assert result == [{"source_id": "1", "status": "updated", "target_id": "abc"}]
    hubspot.read.assert_called_once_with(["1"], service.properties)
    contacts.sync.assert_called_once()
