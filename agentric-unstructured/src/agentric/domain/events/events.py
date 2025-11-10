from typing import override

from .base import BaseEvent


class RequestSubmittedEvent(BaseEvent):
    request_id: str

    @override
    @classmethod
    def get_event_name(cls) -> str:
        return "request_submitted"
