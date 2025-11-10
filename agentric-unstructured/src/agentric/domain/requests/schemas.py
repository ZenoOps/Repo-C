from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from litestar.datastructures import UploadFile
from pydantic import BaseModel, ConfigDict, field_validator

from agentric.db.models.enums import ClaimStatus, SubmissionStatus


class Extraction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    extracted_data: dict[str, Any]

    @field_validator("extracted_data", mode="before")
    @classmethod
    def decode_and_parse_json(cls, value: str | dict) -> dict:
        if isinstance(value, dict):
            return value

        try:
            decoded_bytes = base64.b64decode(value)
            json_string = decoded_bytes.decode("utf-8")
            return json.loads(json_string)
        except (binascii.Error, UnicodeDecodeError):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                msg = "Input string is not valid JSON or Base64-encoded JSON."
                raise ValueError(msg)


@dataclass
class CreateRequestScheama:
    unique_identifier: str  | None = None

@dataclass
class CreateRequest:
    files: list[UploadFile]
    chat_id: UUID | None = None
    unique_identifier: str | None = None


class Request(BaseModel):
    """Pydantic schema for the main Request response.
    Mirrors the SQLAlchemy `Request` model (no extractions).
    """
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    # Base
    id: UUID
    request_number: str
    status: ClaimStatus
    submission_status: SubmissionStatus
    created_at: datetime
    updated_at: datetime
    owner_organization: str | None

    # System fields
    missing_documents: list[str] | None = None
    is_medical_claim: bool = False
    hashed_code: str | None = None
    decision_reason: str | None = None
    payment_status: str | None = None
    payment_reason: str | None = None

    # Claim Info
    claim_number: str | None = None
    claim_amount: str | None = None
    approved_amount: str | None = None
    type_of_claim: str | None = None
    requested_reimbursement_amount: str | None = None
    insurance_agency_name: str | None = None
    premium_amount: str | None = None

    # Trip Info
    trip_start_date: datetime | None = None
    trip_return_date: datetime | None = None
    trip_cost: str | None = None
    destination: str | None = None

    # Client Info
    client_name: str | None = None
    client_email_address: str | None = None
    client_phone_number: str | None = None
    client_post_code: str | None = None
    description: str | None = None

    # Policy Info
    policy_holder: str | None = None
    policy_number: str | None = None
    policy_effective_date: datetime | None = None
    policy_expiration_date: datetime | None = None

    # Broker Info
    broker_name: str | None = None
    broker_email: str | None = None
    broker_commission: str | None = None
    coverage_limits: str | None = None
    maximum_coverage_amount: str | None = None
    created_by: str | None = None
    created_by_id: UUID | None = None
    unique_identifier: str | None = None

class ExtractionResult(BaseModel):
    # Customer info
    customer_name: str | None
    customer_address: str | None
    line_of_business: str | None
    # Broker & policy info
    broker_commission: str | None
    product_type: str | None
    policy_start_date: datetime | None
    policy_end_date: datetime | None

    # Construction data
    business_description: str | None
    buildings: int | None
    construction_wall: str | None
    construction_roof: str | None
    construction_floor: str | None
    construction_frame: str | None
    construction_year_built: int | None
    security: str | None
    sprinkler_effectiveness: str | None
    fire_alarm_effectiveness: str | None
    occupancy: str | None
    number_of_storeys: str | None

    # Fire protection
    fire_protection: str | None

    # Limits of liability
    section_1_material_damage: int | None
    section_2_consequential_loss_business_interruption: int | None
    combined_section_1_and_2: int | None

    # Loss‐or‐damage sub‐limits
    accidental_damage: int | str | None
    burglary_theft_of_property: int | str | None

    # Deductibles
    all_other_losses_section1: int | None
    all_other_losses_section2: int | None

    # missing
    combined_section_1_and_2_deductible: int | None
    contents_stock_in_trade: int | None


class PropertyData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    category: str
    sub_industry: str
    established_and_financially_stable: int
    purpose_built_premises: int
    sprinkler_protected: int
    proactively_risk_managed_and_tested_bcp: int
    engaged_in_legal_and_regulatory_landscape: int


class ClassifedDocument(BaseModel):
    filename: str
    file_type: str


class MissingStatus(BaseModel):
    missing: bool
    reason: str


class MissingAnalysisOutcome(BaseModel):
    claim_type: str
    claim_reason: str
    case_desription: str
    is_hotel_cancellation: bool
    is_hotel_cancellation_reason: str
    deny_status: bool
    deny_reason: str
    missing_status : dict[str, MissingStatus]

class MissingCheckOutcome(BaseModel):

    final_missing_status: bool
    missing_status : dict[str, MissingStatus]
    generated_decision_summary: str | None = None
