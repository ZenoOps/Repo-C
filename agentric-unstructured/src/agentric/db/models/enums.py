from enum import StrEnum


class ChatRole(StrEnum):
    USER = "user_agent"
    ZURICH_REQUEST_AGENT = "insurance_request_agent"
    ZURICH_ANALYST_AGENT = "insurance_analyst_agent"
    ZURICH_GENERAL_AGENT = "zurich_general_agent"
    ZURICH_EMAIL_AGENT = "email_preparation_agent"
    ZURICH_CLAIM_AGENT = "claim_assistant_agent"


class SubmissionStatus(StrEnum):
    PROCESSING = "PROCESSING"  # the request is being processed to be extracted
    INREVIEW = "IN_REVIEW"  # the request is in review
    CLOSED = "CLOSED"  # the request got rejected
    ERROR = "ERROR"  # the request extraction processing failed
    DUPLICATE = "DUPLICATE"  # already have it

class ClaimStatus(StrEnum):
    APPROVED = "APPROVED"  # we want this business
    DECLINED = "DECLINED"  # we don’t want it
    PENDING = "PENDING"  # still deciding
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"
    DECIDING = "DECIDING"
    MISSING = "MISSING"  # missing information
    CLOSED = "CLOSED"
    PAID = "PAID"

class DeclineReason(StrEnum):
    POST_CODE = "POST_CODE"
    WOOD_CONSTRUCTION = "WOOD_CONSTRUCTION"
    INCEPTION_DATE = "INCEPTION_DATE"
    MIN_VALUE = "MIN_VALUE"


class TeamRoles(StrEnum):
    """Valid Values for Team Roles."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
