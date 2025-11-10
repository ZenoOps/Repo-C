from __future__ import annotations

import logging
from typing import final

from litestar import Controller, post

from .base import EventEmitter  # noqa: TC001
from .events import RequestSubmittedEvent

logger = logging.getLogger(__name__)


@final
class EventController(Controller):
    tags = ["Events"]
    path = "/events"

    @post()
    async def send_event(self, event: EventEmitter) -> None:
        """Test emitting an event"""
        event.emit(
            RequestSubmittedEvent(request_id="123"),
        )
