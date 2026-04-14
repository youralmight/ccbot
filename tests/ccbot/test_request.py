"""Unit tests for RetryingHTTPXRequest."""

import pytest
from telegram.error import NetworkError

from ccbot.request import RetryingHTTPXRequest


class TestRetryingHTTPXRequest:
    """Test retry behavior on NetworkError."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self, monkeypatch):
        """First attempt succeeds, no retry needed."""
        call_count = 0

        async def mock_do_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return (200, b'{"ok": true}')

        req = RetryingHTTPXRequest()
        monkeypatch.setattr(
            "ccbot.request.HTTPXRequest.do_request", mock_do_request
        )

        result = await req.do_request()
        assert result == (200, b'{"ok": true}')
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_network_error_then_succeeds(self, monkeypatch):
        """First 2 attempts fail with NetworkError, 3rd succeeds."""
        call_count = 0

        async def mock_do_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(f"Simulated network error {call_count}")
            return (200, b'{"ok": true}')

        req = RetryingHTTPXRequest()
        monkeypatch.setattr(
            "ccbot.request.HTTPXRequest.do_request", mock_do_request
        )

        result = await req.do_request()
        assert result == (200, b'{"ok": true}')
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_reraises_after_max_retries(self, monkeypatch):
        """All attempts fail, NetworkError is re-raised."""
        call_count = 0

        async def mock_do_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise NetworkError("Simulated network error")

        req = RetryingHTTPXRequest()
        monkeypatch.setattr(
            "ccbot.request.HTTPXRequest.do_request", mock_do_request
        )

        with pytest.raises(NetworkError):
            await req.do_request()

        # api_retries defaults to 3, so 4 total attempts (1 + 3 retries)
        assert call_count == 4
