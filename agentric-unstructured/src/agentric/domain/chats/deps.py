"""Chat Controllers."""

from __future__ import annotations

from sqlalchemy.orm import selectinload

from agentric.db import models as m
from agentric.domain.chats.services import ChatMessageService, ChatService
from agentric.lib.deps import create_service_provider

provide_chats_service = create_service_provider(
    ChatService,
    load=[
        # selectinload(m.Chat.messages),
        # selectinload(m.Chat.request),
    ],
    error_messages={"duplicate_key": "This chat already exists.", "integrity": "Chat operation failed."},
)


provide_chat_messages_service = create_service_provider(
    ChatMessageService,
    error_messages={"duplicate_key": "This chat already exists.", "integrity": "Chat operation failed."},
)
