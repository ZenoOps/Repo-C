from typing import Annotated, Literal
from uuid import UUID

import aiofile
from saq import Job, Queue
from structlog import get_logger

from agentric.config import get_settings
from agentric.config.app import alchemy
from agentric.db.models.enums import ClaimStatus, SubmissionStatus
from agentric.domain.chats.deps import provide_chats_service
from agentric.domain.requests.deps import (
    provide_request_attachment_service,
    provide_request_service,
)
from agentric.domain.requests.schemas import Extraction, Request
from agentric.domain.requests.utils import (
    generate_approved_email_template,
    generate_decision_summary,
    generate_decline_email_template,
    generate_missing_email_template,
    generate_partial_payment_email_template,
    get_main_fields,
)

from .schemas import (
    ToolConfirmationReponse,
    ToolEmailResponse,
    ToolFormResponse,
    ToolMessageResponse,
    ToolReponse,
    ToolResultReponse,
)
from .utils import docs_to_string

__all__ = [
    "generate_decline_email",
    "generate_missing_files_email",
    "get_classification",
    "get_decline_reason",
    "get_detail_request",
    "get_request_status",
    "update_request_status",
]

logger = get_logger()
settings = get_settings()

team_folder_path = "./"
API_KEY = settings.app.MODEL_API_KEY
API_BASE_URL = settings.app.API_BASE_URL
queue = Queue.from_url(url=settings.redis.URL, name="agentric_submissions")


async def write_email(request_id: UUID, status: str, email_template_str: str) -> None:
    json_file_path = f"{team_folder_path}/email_{request_id}_{status}.txt"
    async with aiofile.async_open(json_file_path, "w") as f:
        await f.write(email_template_str)


async def get_detail_request(
    request_id: Annotated[UUID, "The Request ID"],
) -> ToolReponse:
    """Get details of the current insuracne request. Use this to get the general details of the request Such as broker information ,
    high level details etc.
    """
    logger.info("Getting details for request_id")

    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
    response = await requests_service.get(item_id=request_id)
    request_details = Request.model_validate(response) if response else None
    await db_session.close()
    return ToolResultReponse(
        type="DETAIL_REQUEST",
        results=[request_details.model_dump(mode="json") if request_details else None],
    )


async def get_classification(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get classification result of the request."""
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get(item_id=request_id)

        extraction = Extraction.model_validate(request.extraction)
        data = get_main_fields(request, extraction.extracted_data)

    await db_session.close()
    return ToolResultReponse(
        type="CLASSIFICATION_REQUEST",
        results=[data],
    )


async def get_request_status(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get status of the request. Use this to get the status of the request"""
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get_one_or_none(id=request_id)

    if request is None:
        return ToolMessageResponse(
            type="SUCCESS",
            message=f"No request found for request_id: {request_id}",
        )
    await db_session.close()
    return ToolMessageResponse(
        type="SUCCESS",
        message=f"Request status: {request.status}",
    )


async def get_decline_reason_tool(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get the decline reason of the request"""
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get_one_or_none(id=request_id)

    if request is None:
        await db_session.close()
        return ToolMessageResponse(
            type="SUCCESS",
            message=f"No request found for request_id: {request_id}",
        )
    if request.status != ClaimStatus.DECLINED:
        await db_session.close()
        return ToolMessageResponse(
            type="SUCCESS",
            message="The request is not in declined status",
        )

    return ToolMessageResponse(
        type="SUCCESS",
        message=request.decision_reason or "Reason not provided",
    )


async def approved_payment_decision(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get(item_id=request_id)

        if request is None:
            return ToolMessageResponse(
                type="SUCCESS",
                message=f"Request {request_id} not found",
            )

        logger.info("yes found the request")
        risk_score = 80.0
        premium_amount = float(request.premium_amount or 0.0)
        if premium_amount == 0.0:
            premium_amount = float(request.approved_amount or 0.0)
        quotation = f"""
**Claim Summary**
- **Risk Score:** {risk_score}
- **Premium Amount:** ${premium_amount:,.2f}
- **Premium Description:** {request.payment_reason}

---

**Policy Coverage Narrative**
{request.description}
---

**Do you confirm this payment approval?**
Please reply **Approved** to accept full-payment approval or **Partial-payment** to accept the claim as partial-payment approval.
"""

        return ToolConfirmationReponse(
            type="CONFIRMATION",
            reason=quotation,
        )


async def get_missing_document_list(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get summary of the request. Use this to get the summary of the request"""
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get(item_id=request_id)
        if request is None:
            return ToolMessageResponse(
                type="SUCCESS",
                message=f"No request found for request_id: {request_id}",
            )

        if request.status != ClaimStatus.MISSING:
            return ToolMessageResponse(
                type="SUCCESS", message="The request is not in missing status"
            )

        if request.missing_documents is None or request.missing_documents == []:
            return ToolMessageResponse(
                type="SUCCESS",
                message="No missing documents found",
            )

        await db_session.close()
        return ToolResultReponse(
            type="CLASSIFICATION_REQUEST",
            results=[
                {
                    "missing_documents": docs_to_string(request.missing_documents),
                }
            ],
        )


async def update_request_status(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
    new_status: Annotated[
        Literal[
            "APPROVED",
            "DECLINED",
            "PENDING",
            "MISSING",
            "CLOSED",
            "PAID",
            "PARTIAL_PAYMENT",
        ],
        "The new status of the request",
    ],
) -> ToolReponse:
    """Change status of the request. Use this to update the status of the request"""
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get_one_or_none(id=request_id)
    update_data = {"status": new_status}
    if request is None:
        return ToolMessageResponse(
            type="SUCCESS",
            message=f"No request found for request_id: {request_id}",
        )

    if new_status == ClaimStatus.PAID:
        update_data["submission_status"] = SubmissionStatus.CLOSED
    else:
        update_data["submission_status"] = SubmissionStatus.INREVIEW

    await requests_service.update(item_id=request_id, data=update_data)
    await db_session.commit()
    await db_session.close()
    return ToolMessageResponse(
        type="SUCCESS",
        message=f"Request status is successfully updated to: {new_status}",
    )


async def get_decline_reason(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get decline reason for the request. Use this when you want to know why a request was declined."""
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None or request.status != ClaimStatus.DECLINED:
            return ToolMessageResponse(
                type="SUCCESS",
                message="The request is not in declined status",
            )

    await db_session.close()

    return ToolConfirmationReponse(
        type="DECLINE_REASON",
        reason=request.decision_reason or "Reason not provided",
    )


async def check_claim_documents(
    chat_id: Annotated[UUID, "Unique Chat ID"],
) -> ToolReponse:
    """Check if the user has uploaded any documents for the request"""

    async with alchemy.get_session() as db_session:
        attachment_service = await anext(provide_request_attachment_service(db_session))
        has_attachment = (await attachment_service.count(chat_id=chat_id)) > 0
        message = (
            "Documents Verified ✅"
            if has_attachment
            else "No doucments found!, Please upload your claim documents first."
        )
        await db_session.close()
        return ToolMessageResponse(
            type="SUCCESS",
            message=message,
        )


async def generate_approve_email(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get email template for approval. Use this when you want to send an approval email."""
    logger.info(
        "Generating email template for approval",
        request_id=request_id,
    )
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))

    request = await requests_service.get_one_or_none(id=request_id)

    ZURICH_EMAIL = "sample_zurich_email@gmail.com"

    if request is None:
        return ToolMessageResponse(
            type="ERROR",
            message=f"No request found for request_id: {request_id}",
        )
    if request.status != ClaimStatus.APPROVED:
        return ToolMessageResponse(
            type="SUCCESS",
            message="Request is not in approved status",
        )

    client_email = request.client_email_address or "client_sample@gmail.com"

    email_template = await generate_approved_email_template(
        from_email=ZURICH_EMAIL,
        to_email=client_email,
        request=request,
    )
    email_template_str = email_template.as_string()
    await write_email(
        email_template_str=email_template_str,
        request_id=request_id,
        status=ClaimStatus.APPROVED.value,
    )
    await db_session.close()
    return ToolEmailResponse(
        type="EMAIL",
        email=str(request_id),
    )


async def generate_partial_payment_email(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get email template for partial-payment. Use this when you want to send a partial-payment email."""
    logger.info(
        "Generating email template for partial-payment",
        request_id=request_id,
    )
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))

    request = await requests_service.get_one_or_none(id=request_id)

    ZURICH_EMAIL = "sample_zurich_email@gmail.com"

    if request is None:
        return ToolMessageResponse(
            type="ERROR",
            message=f"No request found for request_id: {request_id}",
        )
    if request.status != ClaimStatus.PARTIAL_PAYMENT:
        return ToolMessageResponse(
            type="SUCCESS",
            message="Request is not in partial-payment status",
        )

    client_email = request.client_email_address or "client_sample@gmail.com"

    email_template = await generate_partial_payment_email_template(
        from_email=ZURICH_EMAIL,
        to_email=client_email,
        request=request,
    )
    email_template_str = email_template.as_string()
    await write_email(
        email_template_str=email_template_str,
        request_id=request_id,
        status=ClaimStatus.PARTIAL_PAYMENT.value,
    )

    await db_session.close()
    return ToolEmailResponse(
        type="EMAIL",
        email=str(request_id),
    )


async def get_decision_summary(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get decision summary of the request. Use this to get the summary of the request"""
    async with alchemy.get_session() as db_session:
        request_attachment_service = await anext(
            provide_request_attachment_service(db_session)
        )
        chat_service = await anext(provide_chats_service(db_session))
        request_service = await anext(provide_request_service(db_session))
        request = await request_service.get_one_or_none(id=request_id)
        missing_mesg = f"No request found for request_id: {request_id}"
        if request is None:
            return ToolMessageResponse(
                type="SUCCESS",
                message=missing_mesg,
            )

        if request.generated_decision_summary is None or request.generated_decision_summary == "":
            chat_obj = await chat_service.get_one_or_none(request_id=request_id)
            if chat_obj is None:
                return ToolMessageResponse(
                    type="SUCCESS",
                    message=missing_mesg,
                )
            attachments = await request_attachment_service.list(chat_id = chat_obj.id)

            if attachments is None:
                return ToolMessageResponse(
                    type="SUCCESS",
                    message=f"No request attachments found for request_id: {request_id}",
                )

            decision_summary = await generate_decision_summary(
                request=request, attachments=list(attachments)
            )

            request = await request_service.update(
                item_id=request_id,
                data={"generated_decision_summary": decision_summary},
                auto_commit=True
            )

        else:
            decision_summary = request.generated_decision_summary

    return ToolMessageResponse(
        type="SUCCESS",
        message=decision_summary,
    )

async def generate_missing_files_email(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get email template for the missing files of the request. Use this when you want to know why a request was declined."""
    logger.info(
        "Generating email template for missing files for request_id",
        request_id=request_id,
    )
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))

    request = await requests_service.get_one_or_none(id=request_id)

    ZURICH_EMAIL = "sample_zurich_email@gmail.com"

    if request is None:
        return ToolMessageResponse(
            type="ERROR",
            message=f"No request found for request_id: {request_id}",
        )
    if request.status != ClaimStatus.MISSING:
        return ToolMessageResponse(
            type="SUCCESS",
            message="Request is not in missing status",
        )

    missing_files = request.missing_documents or []

    email_template = await generate_missing_email_template(
        missing_files=missing_files,
        from_email=ZURICH_EMAIL,
        to_email=request.client_email_address or "[CLIENT_EMAIL]",
        broker_name=request.client_name or "[CLIENT NAME]",
        request=request,
    )
    email_template_str = email_template.as_string()
    await write_email(
        email_template_str=email_template_str,
        request_id=request_id,
        status=ClaimStatus.MISSING.value,
    )

    await db_session.close()
    return ToolEmailResponse(
        type="EMAIL",
        email=str(request_id),
    )


async def generate_decline_email(
    request_id: Annotated[UUID, "Unique ID for insurance opportunity request"],
) -> ToolReponse:
    """Get email template for the request that was declined. Use this when you want to know why a request was declined."""
    logger.info(
        "Generating decline email template for the request_id",
        request_id=request_id,
    )
    async with alchemy.get_session() as db_session:
        requests_service = await anext(provide_request_service(db_session))
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            return ToolMessageResponse(
                type="ERROR",
                message=f"No request found for request_id: {request_id}",
            )

        if request.status != ClaimStatus.DECLINED:
            return ToolMessageResponse(
                type="ERROR",
                message=f"Request was not declined: {request_id}",
            )
        ZURICH_EMAIL = "sample_zurich_email@gmail.com"

        decline_reason = request.decision_reason

        if decline_reason is None:
            return ToolMessageResponse(
                type="ERROR",
                message=f"The request: {request_id} passed all the decline criterias. Decline reason not found",
            )
        await requests_service.update(
            item_id=request_id, data={"decline_reason": decline_reason}
        )

        decline_email_template = await generate_decline_email_template(
            reasoning=decline_reason,
            from_email=ZURICH_EMAIL,
            to_email=request.client_email_address or "[CLIENT_EMAIL]",
            broker_name=request.client_name or "[CLIENT NAME]",
            request_id=str(request.id),
        )

        email_template_str = decline_email_template.as_string()
        await write_email(
            email_template_str=email_template_str,
            request_id=request_id,
            status=ClaimStatus.DECLINED.value,
        )

        await db_session.close()
        return ToolEmailResponse(
            type="EMAIL",
            email=str(request_id),
        )


async def get_claim_request_status(
    chat_id: Annotated[UUID, "The Unique Chat ID"],
) -> ToolReponse:
    """Get status of the claim request."""
    async with alchemy.get_session() as db_session:
        chat_service = await anext(provide_chats_service(db_session))
        request_service = await anext(provide_request_service(db_session))
        attachment_service = await anext(provide_request_attachment_service(db_session))
        chat_obj = await chat_service.get(item_id=chat_id)
        has_request = chat_obj.request_id
        has_attachment = (await attachment_service.count(chat_id=chat_id)) > 0

        if has_request is None:
            if has_attachment:
                message = f"No request found for chat_id: {chat_id}. User haven't crated a claim request yet!"
            else:
                message = f"No claim request found for chat_id: {chat_id}. User hasn't also uploaded any claim documents."
            return ToolMessageResponse(type="SUCCESS", message=message)
    await db_session.close()

    request = await request_service.get(item_id=chat_obj.request_id)
    if request.submission_status == SubmissionStatus.PROCESSING:
        message = "Your claim request is under data extraction. Please wait a moment."

    else:
        message = "Your claim request is under review."
    await db_session.close()
    return ToolMessageResponse(
        type="SUCCESS",
        message=message,
    )


async def get_travel_plan(
    policy_number: Annotated[str, "Policy Number"],
) -> ToolReponse:
    """Get travel plan."""
    # TODO : Get travel plan from db

    return ToolMessageResponse(
        type="SUCCESS",
        message=f"""
Perfect! Found your policy {policy_number},
Policy for your trip""",
    )


async def create_claim_request(
    chat_id: Annotated[UUID, "The Unique Chat ID"],
) -> ToolReponse:
    async with alchemy.get_session() as db_session:
        chats_service = await anext(provide_chats_service(db_session))
        attachment_service = await anext(provide_request_attachment_service(db_session))
        requests_service = await anext(provide_request_service(db_session))

        chat_obj = await chats_service.get(item_id=chat_id)
        attachments, count = await attachment_service.list_and_count(chat_id=chat_id)
        if chat_obj.request_id is not None:
            message = "User has already create a claim request!"

        elif count <= 0:
            message = " User hasn't uploaded claim documents yet! Please upload claim documents first. ☺️"
        else:
            message = "claim successfully created"

            request_obj = await requests_service.create(
                data={
                    "status": ClaimStatus.PENDING,
                    "submission_status": SubmissionStatus.PROCESSING,
                },
                auto_commit=True,
            )
            request_id = str(request_obj.id)
            for attachment in attachments:

                await attachment_service.update(
                    item_id=attachment.id, data={"request_id": request_id}, auto_commit=True
                )

            await chats_service.update(
                item_id=chat_id, data={"request_id": request_id}, auto_commit=True
            )

            job = Job(
                function="process_submission",
                kwargs={"request_id": request_id},
                timeout=0,
            )
            await queue.enqueue(job)
        logger.info("MEssage 👊")
        logger.info(message)
        await db_session.close()
        return ToolMessageResponse(
            type="SUCCESS",
            message=message,
        )


async def upload_claim_document(
    chat_id: Annotated[UUID, "The Chat ID"],
) -> ToolReponse:

    return ToolFormResponse(
        url=f"{API_BASE_URL}/chats/{chat_id}/submit-claim",
        method="POST",
    )
