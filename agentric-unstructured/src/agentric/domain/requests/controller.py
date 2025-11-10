import asyncio
import mimetypes
import random
import tempfile
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated, Any, Literal
from uuid import UUID

import aiofile
from litestar import Controller, Response, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.response import File
from litestar.response.streaming import Stream
from litestar.serialization import encode_json
from sqlalchemy.exc import NoResultFound
from structlog import getLogger

from agentric.config import get_settings
from agentric.config.base import get_settings
from agentric.db import models as m
from agentric.db.models.enums import ChatRole, ClaimStatus
from agentric.domain.accounts.deps import provide_users_service
from agentric.domain.accounts.guards import requires_active_user
from agentric.domain.accounts.services import UserService
from agentric.domain.chats.deps import provide_chats_service
from agentric.domain.chats.schemas import ToolMessageResponse
from agentric.domain.chats.services import ChatService
from agentric.domain.chats.tools import (
    get_decision_summary,
    get_request_status,
)
from agentric.domain.requests import schemas as s
from agentric.domain.requests.deps import (
    provide_extraction_service,
    provide_request_attachment_service,
    provide_request_service,
)
from agentric.domain.requests.services import (
    RequestAttachmentService,
    RequestService,
)
from agentric.domain.teams.guards import requires_has_one_team
from agentric.lib.utils import read_minio_file
from agentric.domain.requests.utils import generate_followup_question

logger = getLogger()
settings = get_settings()

model_name = settings.app.MODEL_NAME
model_family = settings.app.MODEL_FAIMLY
api_key = settings.app.MODEL_API_KEY


@dataclass
class FileClaim:
    chat_id: str
    attachment_ids: list[str]


@dataclass
class ChatInfo:
    chat_id: str
    request_id: str


async def _rnd_timed_encode_json(data: dict[str, Any]) -> bytes:
    """Randomly encode the JSON data to bytes with a delay"""

    await asyncio.sleep(random.uniform(0.2, 1))
    return encode_json(data) + b"\n"


async def read_email(request_id: UUID, status: str) -> str:
    team_folder_path = "./"
    json_file_path = f"{team_folder_path}/email_{request_id}_{status}.txt"
    async with aiofile.async_open(json_file_path, "r") as f:
        return await f.read()


class RequestController(Controller):
    tags = ["Request"]
    path = "/api/requests"

    dependencies = {
        "users_service": Provide(provide_users_service),
        "chats_service": Provide(provide_chats_service),
        "requests_service": Provide(provide_request_service),
        "extractions_service": Provide(provide_extraction_service),
        "request_attachment_service": Provide(provide_request_attachment_service),
    }

    guards = [requires_active_user]

    @get("/list", guards=[requires_has_one_team])
    async def list_requests(
        self,
        requests_service: RequestService,
        users_service: UserService,
        current_user: m.User,
    ) -> list[s.Request]:
        """List all the child chats for a given chat_id."""

        if current_user.is_superuser:
            requests, _ = await requests_service.list_and_count(
                order_by=[("updated_at", True)],
            )
        else:
            current_user_team = current_user.teams[0]
            requests, _ = await requests_service.list_and_count(
                owner_organization=current_user_team.team_name,
                order_by=[("updated_at", True)],
            )
        response = []
        for req in requests:
            data = requests_service.to_schema(req, schema_type=s.Request)
            if data.created_by_id is not None:
                data.created_by = (
                    await users_service.get(item_id=data.created_by_id)
                ).name
            response.append(data)
        return response

    @get("/{request_id:uuid}")
    async def get_request(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> s.Request:
        """Getthe request of a given request_id."""

        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )

        return requests_service.to_schema(request, schema_type=s.Request)

    @get("/decline_details/{request_id:uuid}")
    async def get_decline_details(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> dict[str, Any]:
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )
        if request.status != ClaimStatus.DECLINED:
            raise NotFoundException(
                detail=f"Request {request_id} hasn't been declined", status_code=404
            )
        extraction = s.Extraction.model_validate(request.extraction)
        return extraction.extracted_data

    @get("/extraction/{request_id:uuid}")
    async def get_extracted_content(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> dict[str, Any]:
        """Get the extracted result of a given request: request_id."""

        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )
        if request.extraction is None:
            raise NotFoundException(
                detail=f"Request {request_id} hasn't been extracted", status_code=404
            )
        extraction = s.Extraction.model_validate(request.extraction)

        return extraction.extracted_data

    @get("/status/{request_id:uuid}")
    async def get_request_status_by_id(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> Response:
        """Get the status of a given request: request_id."""
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )

        return Response(
            content={"request_id": str(request_id), "status": request.status},
            status_code=200,
        )

    @get("/email/{request_id:uuid}")
    async def get_email(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> Response:
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )

        email_str = await read_email(request_id=request_id, status=request.status)
        return Response(
            content={"request_id": str(request_id), "email": email_str},
            status_code=200,
        )

    @post("/delete/{request_id:uuid}")
    async def delete_request(
        self,
        request_id: Annotated[UUID, "The request ID"],
        requests_service: RequestService,
    ) -> Response:
        """Delete the given Chat of the user."""

        try:
            _ = await requests_service.delete(item_id=request_id)

            return Response(
                content={"request_id": str(request_id)},
                status_code=200,
            )

        except NoResultFound:
            raise NotFoundException(
                detail=f"Request ID: {request_id} not found", status_code=404
            )

    @get("/workflow/{request_id:uuid}")
    async def load_request_workflow(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
        step: str,
    ) -> Stream:
        """Get the attachment file of a given request_id request."""

        request = await requests_service.get(item_id=request_id)

        status = request.status

        if status in [
            ClaimStatus.CLOSED,
            ClaimStatus.PENDING,
        ]:
            raise NotFoundException(
                detail=f"Request status is {request.submission_status}. Current workflow is not available for this request.",
                status_code=404,
            )
        return Stream(request_workflow_generator(request=request, stage=step))

    @get("/statistics/{request_id:uuid}")
    async def get_policy_data(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> dict[str, Any]:
        """Get the data of a quotation summary for a given request_id request."""
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )

        if request.extraction is None:
            raise NotFoundException(
                detail=f"Request {request_id} hasn't been extracted", status_code=404
            )

        extraction_obj = request.extraction
        extraction = s.Extraction.model_validate(extraction_obj)

        return extraction.extracted_data["policy_info"]

    @get("/attachments-list/{request_id:uuid}")
    async def list_attachements(
        self,
        request_id: UUID,
        request_attachment_service: RequestAttachmentService,
        chats_service: ChatService,
    ) -> list[dict[str, Any]]:
        chat = await chats_service.get_one_or_none(request_id=request_id)
        if chat is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )
        attachments = list(await request_attachment_service.list(chat_id=chat.id))

        return [
            {"id": str(attachment.id), "file_name": attachment.file_name}
            for attachment in attachments
        ]

    @get("/risk_info/{request_id:uuid}")
    async def get_risk_info(
        self,
        request_id: UUID,
        requests_service: RequestService,
    ) -> dict[str, Any]:
        request = await requests_service.get_one_or_none(id=request_id)

        if request is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )

        return {"data": 0}

    @get("/attachments/{request_attachment_id:uuid}")
    async def get_attachment(
        self,
        request_attachment_id: UUID,
        request_attachment_service: "RequestAttachmentService",
    ) -> Response:
        attachment = await request_attachment_service.get_one_or_none(
            id=request_attachment_id
        )
        if attachment is None:
            raise NotFoundException(
                detail=f"Request attachment {request_attachment_id} not found!",
                status_code=404,
            )

        try:
            content_bytes = await read_minio_file(attachment.url)
            file_name = attachment.file_name
            extension = file_name.split(".")[-1] if "." in file_name else ""

            mime_type, _ = mimetypes.guess_type(file_name)
            if mime_type is None:
                mime_type = "application/octet-stream"

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{extension}"
            ) as tmp_file:
                tmp_file.write(content_bytes)
                tmp_file.flush()
                return File(
                    content_disposition_type="attachment",
                    path=tmp_file.name,
                    filename=file_name,
                    media_type=mime_type,
                )

        except Exception as e:
            raise HTTPException(f"Failed to read document: {e!s}", status_code=500)

    @get("/status_reason/{request_id:uuid}")
    async def get_status_reason(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        requests_service: RequestService,
    ) -> dict[str, str]:
        request = await requests_service.get(item_id=request_id)

        if request.status in [
            ClaimStatus.DECLINED,
            ClaimStatus.APPROVED,
            ClaimStatus.PARTIAL_PAYMENT,
        ]:
            return {"status_reason": request.decision_reason or "Reason not provided"}

        if request.status == ClaimStatus.MISSING:
            reason = "Request is missing information required for claim review. For more information please check in Review session of the chat"

        elif request.status == ClaimStatus.PENDING:
            reason = "Request is under data extraction process"
        elif request.status == ClaimStatus.CLOSED:
            reason = "Claim Request is closed"
        elif request.status == ClaimStatus.PAID:
            reason = "Claim Request is already paid"
        else:
            reason = "Unknown status"

        return {"status_reason": reason}


async def request_workflow_generator(
    request: m.Request,
    stage: str,
) -> AsyncGenerator[bytes, None]:
    try:
        # stage  Literal["initial", "risk_analysis", "quoted"]
        status = request.status
        request_id = request.id
        message_type: Literal["text", "tool_call", "tool_result"] = "text"

        client_name = request.client_name if request.client_name else "N/A"

        if stage == "initial":
            greet = f"New submission received for {client_name}. Document data extraction completed successfully."

            yield await _rnd_timed_encode_json(
                {
                    "type": message_type,
                    "role": ChatRole.ZURICH_GENERAL_AGENT,
                    "message": ToolMessageResponse(
                        type="SUCCESS", message=greet
                    ).model_dump(),
                }
            )
            thoughts = request.generated_thoughts or request.generated_file_check_summary or ""
            insights = "Thoughts: " + thoughts
            yield (
                await _rnd_timed_encode_json(
                    {
                        "type": message_type,
                        "role": ChatRole.ZURICH_ANALYST_AGENT,
                        "message": ToolMessageResponse(
                            type="SUCCESS", message=insights
                        ).model_dump(),
                    }
                )
            )

 
            summary = await get_decision_summary(request_id=request_id)
            if summary is not None:
                yield await _rnd_timed_encode_json(
                    {
                        "type": "tool_result",
                        "role": ChatRole.ZURICH_ANALYST_AGENT,
                        "message": summary.model_dump(),
                    }
                )
            request_status = await get_request_status(request_id=request_id)
            yield (
                await _rnd_timed_encode_json(
                    {
                        "type": "tool_result",
                        "role": ChatRole.ZURICH_REQUEST_AGENT,
                        "message": request_status.model_dump(),
                    }
                )
            )
            generated_follow_up = await generate_followup_question(status=status)
            yield await _rnd_timed_encode_json(
                {
                    "type": message_type,
                    "role": ChatRole.ZURICH_GENERAL_AGENT,
                    "message": {
                        "type": "SUCCESS",
                        "message": generated_follow_up,
                    },
                }
            )

    except Exception as e:
        logger.info(e)
        yield encode_json(
            {
                "type": "error",
                "message": "Internal server error, Please try to reload the chat.",
                "role": ChatRole.ZURICH_GENERAL_AGENT,
            }
        )
