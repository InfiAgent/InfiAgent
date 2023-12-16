# coding: utf-8
from datetime import datetime
from time import time
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ..schemas.agent_models import Message
from ..utils.file_utils import get_file_name_and_path

# Definitions for inputs and outputs schema for /complete api

DEFAULT_TOP_P = 0.7
DEFAULT_TEMPERATURE = 1.0
DEFAULT_STREAM = False

FINISH_STATUS = "FINISH"
FAILED_STATUS = "FAILED"
PROCESSING_STATUS = "PROCESSING"
ASSISTANT = "assistant"


# Main Input Model
class ChatCompleteRequest(BaseModel):
    chat_id: str  # unique chat id for given chat
    code_interpreter: Optional[dict] = {}
    messages: List[dict] = []  # chat message
    model: str = "AZURE_OPEN_AI"  # model name map to LLM conf
    user: str
    max_tokens: Optional[int] = None
    message_conf: Optional[dict] = {}
    n: Optional[int] = None
    plugins: Optional[List[str]] = None
    seed_conf: Optional[dict] = {}
    stream: Optional[bool] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    webgpt: Optional[Dict[str, Any]] = None
    webgpt_network: Optional[bool] = None


class MessageConf(BaseModel):
    top_p: float = DEFAULT_TOP_P
    temperature: float = DEFAULT_TEMPERATURE
    top_k: Optional[int] = None
    time_cost: int
    code_interpreter: dict
    gpt_engine_conf: dict
    stream: bool


class Delta(BaseModel):
    role: str
    content: str
    sid: str
    status: str
    end_turn: bool
    parent_id: str
    children_ids: Optional[Union[List[str], None]]
    err_msg: str
    creator: str
    updater: str
    ctime: str
    utime: str
    message_conf: MessageConf

    def json(self, *args, **kwargs):
        serialized_data = super().json(*args, **kwargs)
        return serialized_data.replace("+00:00", "Z")


class Choice(BaseModel):
    index: int
    delta: Delta
    finish_reason: str


class ChatCompleteResponse(BaseModel):
    id: str
    created: int
    choices: List[Choice]


def chat_request_to_message_conf(chat_request: ChatCompleteRequest) -> MessageConf:
    input_files = {}

    if chat_request.code_interpreter and "tos_key" in chat_request.code_interpreter:
        input_file = chat_request.code_interpreter["tos_key"]
        file_name, tos_path = get_file_name_and_path(input_file)
        input_files = {"tos_key": file_name}

    return MessageConf(
        top_p=chat_request.top_p if chat_request.top_p is not None else DEFAULT_TOP_P,
        temperature=chat_request.temperature if chat_request.temperature is not None else DEFAULT_TEMPERATURE,
        code_interpreter=input_files,
        time_cost=0,
        gpt_engine_conf={},
        stream=chat_request.stream if chat_request.stream is not None else DEFAULT_STREAM
    )


def chat_request_to_deltas(chat_request: ChatCompleteRequest) -> List[Delta]:
    deltas = []
    message_conf = chat_request_to_message_conf(chat_request)

    for message in chat_request.messages:
        delta = Delta(
            role=ASSISTANT,
            content=message["content"],
            sid="",
            status="FINISH",
            end_turn=False,
            parent_id="",
            children_ids=None,
            err_msg="",
            creator=chat_request.user,
            updater=chat_request.user,
            ctime=current_utc_time_as_str(),
            utime=current_utc_time_as_str(),
            message_conf=message_conf
        )
        deltas.append(delta)

    return deltas


def chat_request_to_choices(chat_request: ChatCompleteRequest) -> List[Choice]:
    deltas = chat_request_to_deltas(chat_request)
    choices = []

    for index, delta in enumerate(deltas):
        choice = Choice(
            index=index,
            delta=delta,
            finish_reason="stop"
        )
        choices.append(choice)

    return choices


def chat_request_to_response(chat_request: ChatCompleteRequest) -> ChatCompleteResponse:
    return ChatCompleteResponse(
        id=chat_request.chat_id,
        created=int(time()),
        choices=chat_request_to_choices(chat_request)
    )


def update_chat_response_with_message(chat_response: ChatCompleteResponse,
                                      message: Message,
                                      status: Union[str, None] = None) -> ChatCompleteResponse:
    # Get the last Delta (if exists)
    last_delta = chat_response.choices[-1].delta if chat_response.choices else None
    updated_delta = Delta(
        role=ASSISTANT,  # map with front end
        content=message.content,
        sid=last_delta.sid if last_delta else "",
        status=status if status is not None else FINISH_STATUS,
        end_turn=False,
        parent_id=last_delta.parent_id if last_delta else "",
        children_ids=last_delta.children_ids if last_delta else None,
        err_msg="",
        creator=last_delta.creator if last_delta else None,
        updater=last_delta.updater if last_delta else None,
        ctime=last_delta.ctime if last_delta else current_utc_time_as_str(),
        utime=current_utc_time_as_str(),
        message_conf=MessageConf(
            top_p=last_delta.message_conf.top_p if last_delta and last_delta.message_conf.top_p else DEFAULT_TOP_P,
            temperature=last_delta.message_conf.temperature if last_delta and last_delta.message_conf.temperature else
            DEFAULT_TEMPERATURE,
            code_interpreter=last_delta.message_conf.code_interpreter
            if last_delta and last_delta.message_conf.code_interpreter else {},
            time_cost=0,
            gpt_engine_conf={},
            stream=last_delta.message_conf.stream if last_delta and last_delta.message_conf.stream is not None else
            False
        )
    )

    updated_choice = Choice(
        index=0,  # Since it's the only choice in the list
        delta=updated_delta,
        finish_reason="stop"
    )

    # Update the ChatCompleteResponse to contain only the new Choice
    chat_response.choices = [updated_choice]
    return chat_response


def current_utc_time_as_str() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def create_empty_response():
    # Dummy instance for Delta
    delta = Delta(
        role=ASSISTANT,
        content="",
        sid="",
        status="",
        end_turn=False,
        parent_id="",
        children_ids=None,
        err_msg="",
        creator="",
        updater="",
        ctime="",
        utime="",
        message_conf=MessageConf(
            top_p=0.0,
            temperature=0,
            time_cost=0,
            code_interpreter={},
            gpt_engine_conf={},
            stream=False
        )
    )

    # Dummy instance for Choice
    choice = Choice(
        index=0,
        delta=delta,
        finish_reason=""
    )

    # Dummy instance for ChatCompleteResponse
    response = ChatCompleteResponse(
        id="",
        created=0,
        choices=[choice]
    )
    return response

