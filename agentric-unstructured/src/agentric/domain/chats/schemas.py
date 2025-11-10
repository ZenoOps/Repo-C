from datetime import datetime
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agentric.db.models.enums import ChatRole

T = TypeVar("T")


class StreamChat(BaseModel):
    message: str


class ChatAdd(BaseModel):
    id: UUID
    request_id: UUID


class ToolReponse(BaseModel):
    pass


class ToolResultReponse(ToolReponse, Generic[T]):
    type: Literal[
        "CLASSIFICATION_REQUEST",
        "DETAIL_REQUEST",
        "DECLINE_REASON",
        "NORMAL",
    ]
    results: list[T]


class ToolConfirmationReponse(ToolReponse, Generic[T]):
    type: Literal["APPETITE_APPROVAL", "DECLINE_REASON", "CONFIRMATION"]
    reason: str


class ToolMessageResponse(ToolReponse):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: Literal["SUCCESS", "ERROR"] = "SUCCESS"
    message: str

class ToolFormResponse(ToolReponse):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: Literal["CLAIM_FORM"] = "CLAIM_FORM"
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE"]


class ToolEmailResponse(ToolReponse):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: Literal["EMAIL"] = "EMAIL"
    email: str


class ToolScoreReponse(ToolReponse):
    type: Literal["SCORE"] = "SCORE"
    scores: dict


class ToolAuthURLResponse(ToolReponse):
    type: Literal["AUTH_URL"] = "AUTH_URL"
    url: str
 
class ChatMessage(BaseModel):
    id: UUID
    role: ChatRole
    type: str
    message: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class Chat(BaseModel):
    id: UUID
    request_id: UUID | None
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ChatDetail(BaseModel):
    id: UUID
    request_id: UUID

    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
