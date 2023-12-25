import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
from sse_starlette import EventSourceResponse

from .activity_helpers import (
    async_sse_response_format,
    get_ignore_ping_comment,
    json_response_format,
)


try:
    import infiagent
    from infiagent.schemas import ChatCompleteRequest
    from infiagent.services.complete_local_test import (
        chat_local_event,
        chat_local_event_generator,
    )
    from infiagent.utils import get_logger
except ImportError:
    print("import infiagent failed, please install infiagent by 'pip install .' in the pipeline directory of ADA-Agent")
    from ..schemas import ChatCompleteRequest
    from ..services.complete_local_test import (
        chat_local_event,
        chat_local_event_generator,
    )
    from ..utils import get_logger

logger = get_logger()
local_app = FastAPI()


@local_app.post("/local_sse_test")
async def complete_sse(request: Request):
    body_str = await request.body()

    try:
        chat_request = ChatCompleteRequest.parse_raw(body_str)
        logger.info("Got chat request: {}".format(chat_request))
    except ValidationError as e:
        error_msg = "Invalid input chat_request. Error: {}".format(str(e))
        raise HTTPException(status_code=500, detail=error_msg)

    return EventSourceResponse(async_sse_response_format(chat_local_event_generator(chat_request)),
                               ping_message_factory=get_ignore_ping_comment())


@local_app.post("/local_json_test")
async def complete_json(request: Request):

    body_str = await request.body()

    try:
        chat_request = ChatCompleteRequest.parse_raw(body_str)
        logger.info("Got chat request: {}".format(chat_request))
    except ValidationError as e:
        error_msg = "Invalid input chat_request. Error: {}".format(str(e))
        raise HTTPException(status_code=500, detail=error_msg)

    response_items = await chat_local_event(chat_request)
    return json_response_format(response_items)


@local_app.post("/exception_test")
async def complete_json(request: Request):
    body_str = await request.body()

    try:
        chat_request = ChatCompleteRequest.parse_raw(body_str)
        logger.info("Got chat request: {}".format(chat_request))
    except ValidationError as e:
        error_msg = "Invalid input chat_request. Error: {}".format(str(e))
        raise HTTPException(status_code=500, detail=error_msg)
    return EventSourceResponse(async_sse_response_format(chat_local_event_generator(chat_request)))


async def exception_test(request: Request):
    body_str = await request.body()
    json_val = json.loads(body_str)
    exception_type = json_val.get("exception", None)

    if exception_type:
        raise ValueError("Error triggerd!")
    else:
        yield iter(["Success"])
