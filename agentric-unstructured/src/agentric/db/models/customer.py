from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .request import Request

class Customer(UUIDAuditBase):
    __tablename__ = "customer"
    __table_args__ = {"comment": "Customer data for CRM"}

    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    email_address: Mapped[str | None] = mapped_column(String(255),nullable=True, default=None)
    hashed_name: Mapped[str] =mapped_column(String(length=255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(
        String(length=255), nullable=True, default=None
    )

    requests: Mapped[list[Request]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
