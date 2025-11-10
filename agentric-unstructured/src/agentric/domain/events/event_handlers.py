from __future__ import annotations

import logging

from litestar.events import listener

from .events import RequestSubmittedEvent

logger = logging.getLogger(__name__)


@listener(RequestSubmittedEvent.get_event_name())
async def request_submitted_event_handler(event: RequestSubmittedEvent) -> None:
    """An example event listener"""
    logger.info(f"Request {event.request_id} has been submitted.")  # noqa: G004


LISTENERS = [
    request_submitted_event_handler,
]
