from __future__ import annotations

from advanced_alchemy.repository import (
    SQLAlchemyAsyncRepository,
)
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
)

from agentric.db import models as m


class ChatService(SQLAlchemyAsyncRepositoryService[m.Chat]):
    """Handles database operations for chats."""

    class Repository(SQLAlchemyAsyncRepository[m.Chat]):
        """Chat SQLAlchemy Repository."""

        model_type = m.Chat

    repository_type = Repository


class ChatMessageService(SQLAlchemyAsyncRepositoryService[m.ChatMessage]):
    """Handles database operations for chat messages."""

    class Repository(SQLAlchemyAsyncRepository[m.ChatMessage]):
        """Chat Message SQLAlchemy Repository."""

        model_type = m.ChatMessage

    repository_type = Repository
