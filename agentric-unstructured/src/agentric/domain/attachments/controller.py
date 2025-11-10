import mimetypes
import tempfile
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

from litestar import Controller, Response, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Body
from litestar.response import File
from saq import Queue
from structlog import getLogger

from agentric.config import get_settings
from agentric.config.base import get_settings
from agentric.domain.chats.deps import  provide_chats_service
from agentric.domain.requests.deps import (
    provide_request_attachment_service,
    provide_request_service,
)
from agentric.domain.requests.services import (
    RequestAttachmentService,
)
from agentric.lib.deps import create_filter_dependencies

logger = getLogger()
settings = get_settings()

queue = Queue.from_url(url=settings.redis.URL, name="agentric_submissions")
model_name = settings.app.MODEL_NAME
model_family = settings.app.MODEL_FAIMLY
api_key = settings.app.MODEL_API_KEY


@dataclass
class FileClaim:
    chat_id: str
    attachment_ids: list[str]


class AttachmentController(Controller):
    tags = ["Request"]
    path = "/api/attachments"

    dependencies = {
        "attachment_service": Provide(provide_request_attachment_service),
    } | create_filter_dependencies(
         {
            "id_filter": UUID,
            "search": "request_id,chat_id",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @post("/submit-claim", request_max_body_size=1_073_741_824, exclude_from_auth=True)
    async def submit_claim(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        attachment_service: RequestAttachmentService,
        chat_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> dict[str, str]:

        file = await data.read()

        new_attachment = {"content_bytes": file, "file_name": data.filename}

        if request_id is not None:
            new_attachment["request_id"] = str(request_id)
        if chat_id is not None:
            new_attachment["chat_id"] = str(chat_id)

        try:
            attachment_obj = await attachment_service.create(
                data=new_attachment,auto_commit=True,auto_refresh=True
            )
        except Exception:  # noqa: BLE001
            mesg = "Failed to create attachment! Either request_id or chat_id does not exist"
            raise HTTPException(  # noqa: B904
                detail=mesg,
                status_code=400,
            )

        return {"attachment_id": str(attachment_obj.id)}
