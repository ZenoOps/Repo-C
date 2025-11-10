from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    String,
    Text,
    Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .enums import ClaimStatus, SubmissionStatus

if TYPE_CHECKING:
    from .chat import Chat
    from .customer import Customer
    from .extraction import Extraction


class Request(UUIDAuditBase):
    __tablename__ = "requests"

    hashed_code: Mapped[str | None] = mapped_column(String(2550), nullable=True)
    request_number: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(default=ClaimStatus.PENDING)
    owner_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submission_status: Mapped[SubmissionStatus] = mapped_column(
        default=SubmissionStatus.PROCESSING
    )
    missing_documents: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )

    # LLM Generated Info
    generated_file_check_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_decision_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_of_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_confidence_level: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    is_fraud_suspected: Mapped[bool] = mapped_column(default=False, nullable=True)
    fraud_reasons: Mapped[str] = mapped_column(Text, nullable=True)

    # Calculated Field
    premium_amount: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Claim Info
    claim_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_of_claim: Mapped[str | None] = mapped_column(Text, nullable=True)
    claim_amount: Mapped[str | None] = mapped_column(Text, nullable=True, default="0")
    requested_reimbursement_amount: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    approved_amount: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_coverage_terms: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    insurance_agency_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Trip info
    trip_cost: Mapped[str | None] = mapped_column(Text, nullable=True)
    trip_start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trip_return_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(2550), nullable=True)

    # Client Info
    client_name: Mapped[str | None] = mapped_column(String(2550), nullable=True)
    client_email_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_business_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_post_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Policy Info
    policy_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_holder: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_total_cost: Mapped[str | None] = mapped_column(String(255), nullable=True)
    policy_effective_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    policy_expiration_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


    maximum_coverage_amount: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverage_limits: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Raw extraction payload
    extraction: Mapped["Extraction"] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    generated_decisions: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_thoughts: Mapped[str | None] = mapped_column(Text, nullable=True)
    unique_identifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Relations
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customer.id"), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id"), nullable=True
    )

    customer: Mapped[Customer | None] = relationship(back_populates="requests")
    chat: Mapped["Chat"] = relationship(
        back_populates="request", uselist=False, cascade="all, delete-orphan"
    )
