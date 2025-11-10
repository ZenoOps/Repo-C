from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .request import Request


class Extraction(UUIDAuditBase):
    """Stores the result of a single data extraction attempt from the LLM.
    This is a log, not the final business record.
    """

    __tablename__ = "extractions"

    request_id: Mapped[UUID] = mapped_column(ForeignKey("requests.id"), nullable=False)
    extracted_data: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    request: Mapped["Request"] = relationship(back_populates="extraction")
