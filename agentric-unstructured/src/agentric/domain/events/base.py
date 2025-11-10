from abc import abstractmethod
from typing import Any, final

import msgspec
from litestar import Request


class BaseEvent(msgspec.Struct):
    """Base class for all events"""

    @classmethod
    @abstractmethod
    def get_event_name(cls) -> str:
        """Return the event name"""
        pass


@final
class EventEmitter:
    """Structured event emitter"""

    def __init__(self, request: Request[Any, Any, Any]) -> None:
        self.request = request

    def emit(self, event: BaseEvent) -> None:
        """Emit an event"""
        event_name = event.get_event_name()
        self.request.app.emit(event_name, event=event)
