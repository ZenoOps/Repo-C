import json
import random
import re
import warnings
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated, Literal
from uuid import UUID

from autogen_agentchat.conditions import ExternalTermination
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from litestar import Controller, Request, Response, get, post
from litestar.background_tasks import BackgroundTask
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Stream
from litestar.serialization import encode_json
from saq import Job, Queue
from sqlalchemy.exc import NoResultFound
from structlog import getLogger
from agentric.config import constants
from agentric.config.base import get_settings
from agentric.db import models as m
from agentric.db.models.enums import ChatRole, ClaimStatus, SubmissionStatus
from agentric.domain.accounts.guards import requires_active_user
from agentric.domain.chats.agents import get_agent_team, get_assisant_agent_team
from agentric.domain.chats.deps import (
    provide_chat_messages_service,
    provide_chats_service,
)
from agentric.domain.chats.schemas import (
    Chat,
    ChatMessage,
    StreamChat,
    ToolMessageResponse,
)
from agentric.domain.chats.services import ChatMessageService, ChatService
from agentric.domain.chats.utils import (
    chat_stream,
    customer_chat_stream,
    delete_team_state,
    get_team_state,
)
from agentric.domain.requests.deps import (
    provide_extraction_service,
    provide_request_attachment_service,
    provide_request_service,
)
from agentric.domain.requests.schemas import CreateRequestScheama
from agentric.domain.requests.schemas import Request as RequestSchema
from agentric.domain.requests.services import RequestAttachmentService, RequestService
from agentric.domain.requests.utils import convert_docx_bytes_to_pdf_bytes
from agentric.domain.teams.guards import requires_has_one_team
from agentric.lib.otel import parse_jwt_token
from agentric.lib.utils import read_minio_file, save_file_to_minio

settings = get_settings()
API_BASE_URL = settings.app.API_BASE_URL
USER_AGENT = settings.app.USER_AGENT
llm_name = settings.app.MODEL_NAME

queue = Queue.from_url(url=settings.redis.URL, name="agentric_submissions")

logger = getLogger()
settings = get_settings()

warnings.filterwarnings(
    "ignore", message="Claude models may not work with reflection on tool use*"
)

model_client = OpenAIChatCompletionClient(
    model=settings.app.MODEL_NAME,
    api_key=settings.app.AGENT_API_KEY,
    base_url=settings.app.MODEL_BASE_URL,
    temperature=0.0,
    model_info=ModelInfo(
        vision=False,
        function_calling=True,
        json_output=True,
        family=settings.app.MODEL_FAIMLY,
        structured_output=True,
    ),
)


@dataclass
class UploadFiles:
    files: list[UploadFile]


class ChatController(Controller):
    tags = ["Chat"]
    path = "/api/chats"
    guards = [requires_active_user]

    dependencies = {
        "chats_service": Provide(provide_chats_service),
        "chat_messages_service": Provide(provide_chat_messages_service),
        "requests_service": Provide(provide_request_service),
        "extraction_service": Provide(provide_extraction_service),
        "request_attachment_service": Provide(provide_request_attachment_service),
    }

    @post("/{chat_id:uuid}/submit-claim", request_max_body_size=1_073_741_824)
    async def submit_claim(
        self,
        chat_id: Annotated[UUID, "The Chat ID"],
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        request_attachment_service: RequestAttachmentService,
        chats_service: ChatService,
        current_user: m.User,
    ) -> dict[str, str]:
        file = await data.read()
        chats_obj = await chats_service.get_one_or_none(id=chat_id)

        if chats_obj is None:
            chat_number = str(random.randint(100000, 999999)).zfill(6)
            await chats_service.create(
                data={
                    "id": chat_id,
                    "title": f"#Chat-{chat_number}",
                    "user_id": current_user.id,
                },
                auto_commit=True,
            )
        content = file
        content_type = data.content_type
        file_name = data.filename

        if (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            content_type = "application/pdf"
            content = convert_docx_bytes_to_pdf_bytes(file)
            file_name = file_name.replace(".docx", ".pdf")
        url = await save_file_to_minio(
            filename=file_name, content=content, content_type=content_type
        )
        attachment = await request_attachment_service.create(
            data={"chat_id": chat_id, "url": url, "file_name": file_name},
            auto_commit=True,
        )
        return {"attachment_id": str(attachment.id)}

    @post(
        "/{chat_id:uuid}/create-claim",
        request_max_body_size=1_073_741_824,
        guards=[requires_has_one_team],
    )
    async def create_request(
        self,
        request: Request,
        data: Annotated[
            CreateRequestScheama, Body(media_type=RequestEncodingType.MULTI_PART)
        ],
        chat_id: Annotated[UUID, "The Chat ID"],
        requests_service: RequestService,
        chats_service: ChatService,
        request_attachment_service: RequestAttachmentService,
        current_user: m.User,
    ) -> RequestSchema:
        """Create a new request"""

        chat_obj = await chats_service.get_one_or_none(id=chat_id)
        if chat_obj is None:
            raise NotFoundException(detail=f"Chat {chat_id} not found", status_code=404)

        attachments = await request_attachment_service.list(chat_id=chat_id)

        if len(attachments) <= 0:
            raise NotFoundException(detail="No attachments found", status_code=404)
        user_team = current_user.teams[0].team_name
        new_request_data = {
            "owner_organization": user_team,
            "created_by_id": current_user.id,
            "status": ClaimStatus.PENDING,
            "submission_status": SubmissionStatus.PROCESSING,
        }
        if data.unique_identifier is not None:
            new_request_data["unique_identifier"] = data.unique_identifier

        request_obj = await requests_service.create(
            data=new_request_data,
            auto_commit=True,
        )
        request_id = str(request_obj.id)
        await chats_service.update(
            item_id=chat_id, data={"request_id": request_id}, auto_commit=True
        )
        auth = request.headers.get("authorization")

        if not auth:
            raise NotFoundException(detail="Missing Authorization header")

        payload = parse_jwt_token(auth)
        session_id = payload.get("jti") or ""

        function_name = "process_covermore_claims" if user_team == constants.cover_more_team else "process_travelguard_claims"
        job = Job(
            function=function_name,
            kwargs={
                "request_id": request_id,
                "session_id": session_id,
                "user_id": str(current_user.id),
                "user_email": current_user.email,
            },
            timeout=0,
        )
        _ = await queue.enqueue(job)

        await queue.info(jobs=True)

        return requests_service.to_schema(data=request_obj, schema_type=RequestSchema)

    @get("/list")
    async def list_chats(self, chats_service: ChatService) -> list[Chat]:
        """List all the child chats for a given chat_id."""

        chats, _ = await chats_service.list_and_count(order_by=m.Chat.created_at.desc())
        return [chats_service.to_schema(chat, schema_type=Chat) for chat in chats]

    @get("/messages/{chat_id: uuid}")
    async def list_chat_messages(
        self,
        chat_id: Annotated[UUID, "The Chat ID"],
        chats_service: RequestService,
        chat_messages_service: ChatService,
    ) -> list[ChatMessage]:
        """List all chat messages of the child chat_id."""

        chat_obj = await chats_service.get_one_or_none(id=chat_id)

        if chat_obj is None:
            raise NotFoundException(
                detail=f"Chat {chat_obj} not found", status_code=404
            )
        chat_messages, _ = await chat_messages_service.list_and_count(
            chat_id=chat_obj.id
        )
        return [
            chat_messages_service.to_schema(message, schema_type=ChatMessage)
            for message in chat_messages
        ]

    @post("/{chat_id: uuid}/delete", exclude_from_auth=True)
    async def delete_chat(
        self, chat_id: Annotated[UUID, "The chat ID"], chats_service: ChatService
    ) -> Response:
        """Delete the given Chat of the user."""

        try:
            _ = await chats_service.delete(item_id=chat_id)

            return Response(
                content={"chat_id": str(chat_id)},
                status_code=200,
                # Delete the team state by off-loading with background task
                background=BackgroundTask(delete_team_state, str(chat_id)),
            )

        except NoResultFound:
            raise NotFoundException(  # noqa: B904
                detail=f"User's Chat {chat_id} not found", status_code=404
            )

    @get("/requests/{request_id: uuid}")
    async def get_chat_id(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        chats_service: ChatService,
    ) -> dict[str, str] | None:
        """Retrieve the Chat of the given Request ."""

        chat = await chats_service.get_one_or_none(request_id=request_id)

        return {"chat_id": str(chat.id)} if chat else None

    @get("/{request_id: uuid}")
    async def get_chat_by_request_id(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        chats_service: ChatService,
    ) -> m.Chat | None:
        """Retrieve the Chat of the given Request ."""

        return await chats_service.get_one_or_none(request_id=request_id)

    @get("/chat-id/{request_id: uuid}")
    async def get_chat_by_chat_id(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        chats_service: ChatService,
    ) -> m.Chat | None:
        """Retrieve the Chat of the given Request ."""

        return await chats_service.get_one_or_none(request_id=request_id)

    @get("/chat-messages/{chat_id: uuid}")
    async def get_chat_messages(
        self,
        chat_id: Annotated[UUID, "The Chat ID"],
        chat_messages_service: ChatMessageService,
    ) -> list[ChatMessage]:
        """Retrieve the Chat of the given Request ."""

        chat_messages, _ = await chat_messages_service.list_and_count(
            chat_id=chat_id, order_by=m.ChatMessage.created_at.desc()
        )
        return [
            chat_messages_service.to_schema(message, schema_type=ChatMessage)
            for message in chat_messages
        ]

    @post("/clean/{request_id:uuid}")
    async def clean_state(
        self,
        request_id: Annotated[UUID, "The Request ID"],
        chats_service: ChatService,
    ) -> Response:
        """Clean the Chat states"""

        chat = await chats_service.get_one_or_none(request_id=request_id)

        if chat is None:
            raise NotFoundException(
                detail=f"Request {request_id} not found", status_code=404
            )

        # Delete the team state by off-loading with background task
        delete_team_state(str(chat.id))

        return Response(
            content={"request_id": str(request_id)},
            status_code=200,
        )

    @post("/stream/{request_id: uuid}")
    async def stream_chat(
        self,
        request_id: Annotated[UUID, "The Request UUID"],
        data: StreamChat,
        chats_service: ChatService,
        chat_messages_service: ChatMessageService,
        requests_service: RequestService,
    ) -> Stream:
        """Chat with the Agent."""

        user_input = data.message.strip()

        req_obj = await requests_service.get_one_or_none(id=request_id)

        if req_obj is None:
            raise NotFoundException(detail="Request not found", status_code=404)

        current_chat = req_obj.chat

        if current_chat is None:
            current_chat = await chats_service.create(
                data={"request_id": request_id, "title": "New Chat"}
            )

        system_message = f"""
        Here is the request_id that you are working on: {request_id}. It status is {req_obj.status}
        """

        external_termination = ExternalTermination()
        chat_id_str = str(current_chat.id)

        agent_team = await get_agent_team(
            model_client, external_termination, system_message
        )

        team_state = await get_team_state(chat_id_str)

        if team_state is not None:
            await agent_team.load_state(team_state)

        return Stream(
            chat_stream(
                team=agent_team,
                chat_id=chat_id_str,
                user_input=user_input,
                termination=external_termination,
                chat_messages_service=chat_messages_service,
            )
        )

    @post("/customer-assistant/stream/{chat_id: uuid}")
    async def customer_agent_stream_chat(
        self,
        chat_id: Annotated[UUID, "The Request UUID"],
        data: StreamChat,
        chats_service: ChatService,
        chat_messages_service: ChatMessageService,
        requests_service: RequestService,
        request_attachment_service: RequestAttachmentService,
        current_user: m.User,
    ) -> Stream:
        """Chat with the Agent."""

        user_input = data.message.strip()

        chat_obj = await chats_service.get_one_or_none(id=chat_id)

        if chat_obj is None:
            chat_number = str(random.randint(100000, 999999)).zfill(6)
            chat_obj = await chats_service.create(
                data={
                    "id": chat_id,
                    "title": f"#Chat-{chat_number}",
                    "user_id": current_user.id,
                }
            )
        elif chat_obj.request_id and chat_obj.title == "New Chat":
            request = await requests_service.get(item_id=chat_obj.request_id)
            chat_obj = await chats_service.update(
                item_id=chat_id, data={"title": f"#{request.request_number}"}
            )

        custom_message = f"Here is the chat_id that you are working on: {chat_id!s}."

        external_termination = ExternalTermination()
        chat_id_str = str(chat_obj.id)

        agent_team = await get_assisant_agent_team(
            model_client, external_termination, custom_message
        )

        team_state = await get_team_state(chat_id_str)

        if team_state is not None:
            logger.info("Found the team state")
            await agent_team.load_state(team_state)

        match = re.search(r'(\{.*?"UPLOADED_DOC_IDs".*?\})', user_input)

        file_history = []
        if match:
            json_part = match.group(1)
            user_input = user_input.replace(json_part, "").strip()
            document_dict = json.loads(json_part)
            document_ids = document_dict["UPLOADED_DOC_IDs"]
            for document_id in document_ids:
                attachment = await request_attachment_service.get_one_or_none(
                    id=document_id
                )

                if attachment is None:
                    continue
                content_bytes = await read_minio_file(attachment.url)

                file_mesg = {
                    "type": "FILE",
                    "message": {
                        "file_name": attachment.file_name,
                        "file_size": len(content_bytes),
                    },
                }

                file_history.append(
                    {
                        "chat_id": chat_id,
                        "type": "tool_result",
                        "role": "user_agent",
                        "message": f"```json\n{json.dumps(file_mesg)}\n```",
                    }
                )

        return Stream(
            customer_chat_stream(
                team=agent_team,
                chat_id=chat_id_str,
                user_input=user_input,
                termination=external_termination,
                chat_messages_service=chat_messages_service,
                file_history=file_history,
            )
        )

    @get("/workflow/{chat_id:uuid}")
    async def load_request_workflow(
        self,
        chat_id: Annotated[UUID, "The Request ID"],
        chats_service: ChatService,
        current_user: m.User,
        step: str,
    ) -> Stream:
        """Get the attachment file of a given request_id request."""

        return Stream(
            request_workflow_generator(
                customer_name=current_user.name or "John", stage=step
            )
        )


async def request_workflow_generator(
    customer_name: str,
    stage: str,
) -> AsyncGenerator[bytes, None]:
    try:
        # stage  Literal["initial", "risk_analysis", "quoted"]

        message_type: Literal["text", "tool_call", "tool_result"] = "text"

        if stage == "initial":
            greet = f"Hello! {customer_name}, I'm a Agentric Travel Insurance Assistant. How can I help you today?"

            yield encode_json(
                {
                    "type": message_type,
                    "role": ChatRole.ZURICH_CLAIM_AGENT,
                    "message": ToolMessageResponse(
                        type="SUCCESS", message=greet
                    ).model_dump(),
                }
            )

    except Exception as e:
        logger.info("Chat failed")
        logger.info(e)
        yield encode_json(
            {
                "type": "error",
                "message": "Internal server error, Please try to reload the chat.",
                "role": ChatRole.ZURICH_GENERAL_AGENT,
            }
        )
