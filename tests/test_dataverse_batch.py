from unittest import mock

from src.dynamics.batch import BatchRequest, DataverseBatch


def test_batch_builds_read_requests_and_parses_statuses():
    client = mock.Mock()
    client.base_url = "https://example.crm.dynamics.com/api/data/v9.2"
    client.timeout = 30.0
    client.auth.get_access_token.return_value = "token"

    response = mock.Mock()
    response.text = (
        "Content-ID: one\r\nHTTP/1.1 200 OK\r\n"
        "Content-ID: two\r\nHTTP/1.1 404 Not Found\r\n"
    )
    client.session.post.return_value = response

    batch = DataverseBatch(client)
    result = batch.execute([
        BatchRequest("contacts?$top=1", "one"),
        BatchRequest("opportunities?$top=1", "two"),
    ])

    assert result == {"one": 200, "two": 404}
    body = client.session.post.call_args.kwargs["data"]
    assert "GET https://example.crm.dynamics.com/api/data/v9.2/contacts?$top=1 HTTP/1.1" in body
    assert "GET https://example.crm.dynamics.com/api/data/v9.2/opportunities?$top=1 HTTP/1.1" in body
