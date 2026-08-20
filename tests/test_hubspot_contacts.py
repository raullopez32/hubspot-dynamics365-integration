from unittest import mock

from src.hubspot.contacts import HubSpotContacts


def test_list_members_follows_paging():
    client = mock.Mock()
    client.request.side_effect = [
        {
            "results": [{"recordId": "1"}],
            "paging": {"next": {"after": "next"}},
        },
        {"results": [{"recordId": "2"}]},
    ]

    contacts = HubSpotContacts(client)

    assert contacts.list_members("123") == ["1", "2"]


def test_read_splits_batches_of_100():
    client = mock.Mock()
    client.request.side_effect = [
        {"results": [{"id": str(i)} for i in range(100)]},
        {"results": [{"id": "100"}]},
    ]
    contacts = HubSpotContacts(client)

    result = contacts.read([str(i) for i in range(101)], ["email"])

    assert len(result) == 101
    assert client.request.call_count == 2
