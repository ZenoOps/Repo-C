from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import EventEmitter

if TYPE_CHECKING:
    from litestar import Request


async def provide_event_emitter(request: Request[Any, Any, Any]) -> EventEmitter:
    return EventEmitter(request)
