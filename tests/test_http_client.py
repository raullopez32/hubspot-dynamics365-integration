from src.http_client import RETRYABLE_METHODS, RETRYABLE_STATUS_CODES, build_retry_session


def test_retry_session_only_retries_safe_methods():
    session = build_retry_session(retries=2, backoff_factor=0.1)
    retry = session.get_adapter("https://").max_retries

    assert retry.total == 2
    assert retry.allowed_methods == RETRYABLE_METHODS
    assert set(retry.status_forcelist) == set(RETRYABLE_STATUS_CODES)
    assert "POST" not in retry.allowed_methods
    assert "PATCH" not in retry.allowed_methods
