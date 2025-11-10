from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, asc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentric.db.models.request import Request

from .chat_message import ChatMessage

if TYPE_CHECKING:
    from .request_attachment import RequestAttachment

class Chat(UUIDAuditBase):
    __tablename__ = "chats"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(nullable=False)

    # One request → one chat
    request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("requests.id", ondelete="SET NULL"),
        unique=True,  # 🔹 ensures one chat per request
        nullable=True,
    )

    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    request: Mapped["Request | None"] = relationship(
        back_populates="chat",
        passive_deletes=True,
        lazy="raise"  # prevents auto lazy-loading during update
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by=lambda: asc(ChatMessage.created_at),
    )

    attachments: Mapped[list["RequestAttachment"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
    )
