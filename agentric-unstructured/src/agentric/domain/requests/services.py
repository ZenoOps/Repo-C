from __future__ import annotations

import random
import string
import uuid
from typing import Any


from advanced_alchemy.repository import (
    SQLAlchemyAsyncRepository,
)
from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
)

from agentric.db import models as m
import shortuuid
from advanced_alchemy.utils.dataclass import Empty
from advanced_alchemy.exceptions import ErrorMessages


async def generate_request_number() -> str:


    letters = "".join(random.choices(string.ascii_letters, k=3))

    numbers = "".join(random.choices(string.digits, k=3))

    uuid_part = shortuuid.uuid()
    return f"{letters}{numbers}{uuid_part}"

class RequestService(SQLAlchemyAsyncRepositoryService[m.Request]):
    """Handles database operations for requests."""

    class Repository(SQLAlchemyAsyncRepository[m.Request]):
        """Request SQLAlchemy Repository."""

        model_type = m.Request

    repository_type = Repository

    async def create(
        self,
        data: ModelDictT[m.Request] | dict[str, Any],
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
        error_messages: ErrorMessages | type[Empty] | None = None,
    ) -> m.Request:
        """Wrap repository instance creation.

        Args:
            data: Representation to be created.
            auto_expunge: Remove object from session before returning.
            auto_refresh: Refresh object from session before returning.
            auto_commit: Commit objects before returning.
            error_messages: An optional dictionary of templates to use
                for friendlier error messages to clients

        Returns:
            Representation of created instance.
        """
        if not isinstance(data, dict):
            data = data.to_dict()

        data["request_number"] =  await generate_request_number()


        data = await self.to_model(data, "create")
        return await self.repository.add(
            data=data,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            auto_refresh=auto_refresh,
            error_messages=error_messages,
        )


class ExtractionService(SQLAlchemyAsyncRepositoryService[m.Extraction]):
    """Handles database operations for extractions."""

    class Repository(SQLAlchemyAsyncRepository[m.Extraction]):
        """Extraction SQLAlchemy Repository."""

        model_type = m.Extraction

    repository_type = Repository



class RequestAttachmentService(SQLAlchemyAsyncRepositoryService[m.RequestAttachment]):
    """Handles database operations for RequestAttachment."""

    class Repository(SQLAlchemyAsyncRepository[m.RequestAttachment]):
        """Request Attachment SQLAlchemy Repository."""

        model_type = m.RequestAttachment

    repository_type = Repository
