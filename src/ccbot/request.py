"""Custom HTTPXRequest with tenacity retry on NetworkError.

Subclasses PTB's HTTPXRequest and wraps do_request() with tenacity retry,
covering all Telegram API calls (send, edit, delete, get_file, download, etc.)
at a single point without modifying individual call sites.
"""

import logging
from typing import Any

from telegram.error import NetworkError
from telegram.request import HTTPXRequest
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from .config import config

logger = logging.getLogger(__name__)


class RetryingHTTPXRequest(HTTPXRequest):
    """HTTPXRequest that retries on NetworkError with exponential backoff."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._retry_logger = logging.getLogger("tenacity")

    async def do_request(self, *args: Any, **kwargs: Any) -> tuple[int, bytes]:
        @retry(
            retry=retry_if_exception_type(NetworkError),
            stop=stop_after_attempt(config.api_retries + 1),
            wait=wait_exponential(min=1, max=8),
            reraise=True,
            before_sleep=before_sleep_log(self._retry_logger, logging.WARNING),
        )
        async def _inner() -> tuple[int, bytes]:
            return await super(RetryingHTTPXRequest, self).do_request(*args, **kwargs)

        return await _inner()
