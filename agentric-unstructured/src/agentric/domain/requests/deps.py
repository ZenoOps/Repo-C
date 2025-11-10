"""Chat Controllers."""

from __future__ import annotations

from sqlalchemy.orm import selectinload

from agentric.db import models as m
from agentric.domain.requests.services import ExtractionService, RequestAttachmentService, RequestService
from agentric.lib.deps import create_service_provider

__all__ = ("provide_extraction_service", "provide_request_service")

provide_extraction_service = create_service_provider(
    ExtractionService,

    error_messages={"duplicate_key": "This extraction already exists.", "integrity": "Extraction failed."},
)


provide_request_service = create_service_provider(
    RequestService,
    load=[
        selectinload(m.Request.extraction),
        selectinload(m.Request.chat),
    ],

    error_messages={"duplicate_key": "This request already exists.", "integrity": "Request operation failed."},
)


provide_request_attachment_service = create_service_provider(
    RequestAttachmentService,
    error_messages={"duplicate_key": "This requset attachment already exists.", "integrity": "Request Attachment operation failed."},
)

