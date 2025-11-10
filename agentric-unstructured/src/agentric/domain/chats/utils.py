import io
import json
import os
import re
import tempfile
from collections.abc import AsyncGenerator
from typing import Any, Literal

import aiofile
import httpx
import mammoth
from autogen_agentchat.conditions import ExternalTermination
from autogen_agentchat.messages import (
    MemoryQueryEvent,
    ThoughtEvent,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
    UserInputRequestedEvent,
)
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core import CancellationToken
from autogen_core.models import FunctionExecutionResultMessage
from litestar.serialization import encode_json
from structlog import getLogger


from agentric.config import get_settings
from agentric.domain.chats.services import ChatMessageService

__all__ = [
    "delete_team_state",
    "get_team_state",
]

settings = get_settings()
logger = getLogger()

API_BASE_URL = settings.app.API_BASE_URL
USER_AGENT = settings.app.USER_AGENT

team_folder_path = settings.app.TEAM_STATE_FOLDER_PATH
llm_name = settings.app.MODEL_NAME


async def async_read_json(json_file_path: str) -> dict[str, Any]:
    if os.path.exists(json_file_path):
        async with aiofile.async_open(json_file_path, "r") as f:
            content = await f.read()

            if content:
                return json.loads(content)

    return {}


async def get_team_state(
    chat_id: str,
) -> dict[str, Any] | None:

    state_file_path = os.path.join(f"{chat_id}.json")
    logger.info("state file loading")
    if os.path.exists(state_file_path):
        logger.info("state file found")
        return await async_read_json(state_file_path)

    return None


def docs_to_string(docs: list[str]) -> str:
    def nice(name: str) -> str:
        base = name.split(".", 1)[0]
        base = re.sub(r"[_-]+", " ", base).strip()
        return base.title()

    n = len(docs)
    if n == 0:
        return ""
    if n == 1:
        return nice(docs[0])
    if n == 2:
        return f"{nice(docs[0])} and {nice(docs[1])}"
    return ", ".join(nice(x) for x in docs[:-1]) + f" and {nice(docs[-1])}"


async def make_request(
    url: str,
    method: str = "GET",
    data: dict[str, Any] = {},
) -> dict[str, Any]:
    """Make a request to the API with proper error handling.

    Args:
        url (str): The URL to make the request to.
        chat_id (str): The session ID to use for authentication.
        method (str, optional): The HTTP method to use. Defaults to "GET".
        data (dict[str, Any], optional): The data to send with the request. Defaults to None.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            if method == "POST":
                response = await client.post(
                    url, headers=headers, timeout=30.0, json=data
                )
            else:
                response = await client.get(url, headers=headers, timeout=30.0)

            if response.status_code == 401:
                return {"error": "Unauthorized request."}

            data = response.json()

            logger.info(f"Json response of {url}")
            logger.info(data)
            return data
        except Exception:
            return {"error": "Unexpected error occurred. Please try again later."}


async def chat_stream(
    chat_id: str,
    team: SelectorGroupChat,
    user_input: str,
    termination: ExternalTermination,
    chat_messages_service: ChatMessageService,
) -> AsyncGenerator[bytes, None]:

    stream = team.run_stream(task=user_input, cancellation_token=CancellationToken())

    conversations = []
    try:
        async for message in stream:
            # skip internals
            if isinstance(
                message, (ToolCallExecutionEvent, MemoryQueryEvent, ThoughtEvent)
            ):
                continue

            message_type: Literal["text", "tool_call", "tool_result"] = "text"
            source = getattr(message, "source", "")
            content = getattr(message, "content", "")

            if isinstance(message, UserInputRequestedEvent):
                logger.info("Caught UserInputRequestedEvent")
                termination.set()
                break

            if source == "":
                continue

            new_chat_message = {
                "chat_id": chat_id,
                "message": content,
                "role": source,
                "type": message_type,
            }
            if source in {"user", "user_proxy", "user_agent"}:
                continue

            if "TERMINATE" in content:
                content = content.split("TERMINATE", 1)[0].strip()

            if isinstance(message, ToolCallRequestEvent):
                tool_name = message.content[0].name
                new_chat_message["message"] = f"Calling tool: {tool_name}"
                new_chat_message["type"] = "tool_call"
                message_type = "tool_call"
                content = new_chat_message["message"]

            if isinstance(
                message, (FunctionExecutionResultMessage, ToolCallSummaryMessage)
            ):
                logger.info("FUnction tool exec")
                item = (
                    message.content[0]
                    if isinstance(message.content, list)
                    else message.content
                )
                tool_name = getattr(item, "name", "Tool execution result")
                tool_result = getattr(item, "content", item)
                new_chat_message["type"] = "tool_result"
                new_chat_message["message"] = f"```json\n{tool_result}\n```"
                message_type = "tool_result"
                content = new_chat_message["message"]

            conversation = {"type": message_type, "role": source, "message": content}
            yield encode_json(conversation) + b"\n"
            conversations.append({"chat_id": chat_id, **conversation})
            continue

    except Exception as e:
        logger.info(e)

        err = {"role": "system", "message": " An error occurred—please try again."}
        yield (json.dumps(err) + "\n").encode("utf-8")
    finally:
        team_state = await team.save_state()

        await save_team_state(
            chat_id,
            json.dumps(team_state, ensure_ascii=False, indent=2, default=str),
        )
        await chat_messages_service.create_many(conversations, auto_commit=True)


async def customer_chat_stream(
    chat_id: str,
    team: SelectorGroupChat,
    user_input: str,
    termination: ExternalTermination,
    chat_messages_service: ChatMessageService,
    file_history: list | None = None,
) -> AsyncGenerator[bytes, None]:

    stream = team.run_stream(task=user_input, cancellation_token=CancellationToken())
    conversations = []
    if file_history is not None:
        conversations = file_history

    conversations.append(
        {
            "chat_id": chat_id,
            "type": "text",
            "role": "user_agent",
            "message": user_input,
        }
    )
    file_upload_flag = False
    skip_cache = False
    try:
        async for message in stream:
            if isinstance(message, ThoughtEvent):
                if message.content and message.source:
                    conversation = {
                        "type": "text",
                        "role": message.source,
                        "message": message.content.strip(),
                    }
                    yield encode_json(conversation) + b"\n"
                    conversations.append({"chat_id": chat_id, **conversation})
                continue

            if isinstance(message, (ToolCallExecutionEvent, MemoryQueryEvent)):
                continue

            message_type: Literal["text", "tool_call", "tool_result"] = "text"
            source = getattr(message, "source", "")
            content = getattr(message, "content", "")

            if isinstance(message, UserInputRequestedEvent):
                logger.info("Caught UserInputRequestedEvent")
                termination.set()
                break

            if not source:
                continue

            if source in {"user", "user_proxy", "user_agent"}:
                continue

            if isinstance(content, str) and "TERMINATE" in content:
                content = content.split("TERMINATE", 1)[0].strip()

            if isinstance(message, ToolCallRequestEvent):
                tool_name = message.content[0].name
                if tool_name == "initiate_claim_document_upload_ui":
                    file_upload_flag = True
                content = f"Calling tool: {tool_name}"
                message_type = "tool_call"

            elif isinstance(
                message, (FunctionExecutionResultMessage, ToolCallSummaryMessage)
            ):
                logger.info("Function tool exec")
                if file_upload_flag:
                    file_upload_flag = False
                    skip_cache = True
                item = (
                    message.content[0]
                    if isinstance(message.content, list)
                    else message.content
                )
                tool_result = getattr(item, "content", item)
                content = f"```json\n{tool_result}\n```"
                message_type = "tool_result"

            conversation = {"type": message_type, "role": source, "message": content}
            yield encode_json(conversation) + b"\n"
            if skip_cache:
                skip_cache = False
                continue
            conversations.append({"chat_id": chat_id, **conversation})

    except Exception as e:
        logger.info(e)
        err = {"role": "system", "message": "An error occurred—please try again."}
        yield (json.dumps(err) + "\n").encode("utf-8")

    finally:
        team_state = await team.save_state()

        await save_team_state(
            chat_id,
            json.dumps(team_state, ensure_ascii=False, indent=2, default=str),
        )
        chat_messages = await chat_messages_service.create_many(
            conversations, auto_commit=True
        )
        logger.info("Chat message create")
        logger.info(len(chat_messages))


async def save_team_state(chat_id: str, team_state: str) -> None:
    logger.info("Saving team state: " + str(chat_id))
    state_file_path = os.path.join(f"{chat_id}.json")
    async with aiofile.async_open(state_file_path, "w") as f:
        await f.write(team_state)


def delete_team_state(chat_id: str) -> None:
    state_file_path = os.path.join(f"{chat_id}.json")

    if os.path.exists(state_file_path):
        logger.info("Found the state file")
        try:
            os.remove(state_file_path)
            logger.info("State file deleted successfully.")
        except OSError as e:
            logger.error(f"Failed to delete state file: {e}")
    else:
        logger.info("State file not found.")
