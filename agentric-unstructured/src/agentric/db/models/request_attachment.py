from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentric.db.models.request import Request

if TYPE_CHECKING:
    from .chat import Chat

class RequestAttachment(UUIDAuditBase):
    __tablename__ = "request_attachments"

    chat_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chats.id"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(String(250), nullable=False)
    chat: Mapped["Chat | None"] = relationship(back_populates="attachments")
