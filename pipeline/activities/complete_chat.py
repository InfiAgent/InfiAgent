from fastapi import APIRouter, Request, HTTPException
from pydantic import ValidationError
from sse_starlette import EventSourceResponse, ServerSentEvent

from .activity_helpers import async_sse_response_format, IGNORE_PING_COMMENT, json_response_format

try:
    import infiagent
    from infiagent.db.conversation_dao import ConversationDAO
    from infiagent.schemas import ChatCompleteRequest
    from infiagent.services.chat_complete_sse_service import chat_event_generator, chat_event_response
    from infiagent.tools.code_sandbox.async_sandbox_client import AsyncSandboxClient
    from infiagent.utils import get_logger
except ImportError:
    print("import infiagent failed, please install infiagent by 'pip install .' in the pipeline directory of ADA-Agent")    
    from ..db.conversation_dao import ConversationDAO
    from ..schemas import ChatCompleteRequest
    from ..services.chat_complete_sse_service import chat_event_generator, chat_event_response
    from ..tools.code_sandbox.async_sandbox_client import AsyncSandboxClient
    from ..utils import get_logger

complete_chat_router = APIRouter()
logger = get_logger()


@complete_chat_router.post("/complete_sse")
async def complete_sse(request: Request):
    body_str = await request.body()

    try:
        chat_request = ChatCompleteRequest.parse_raw(body_str)
        logger.info("Got chat request: {}".format(chat_request))
    except ValidationError as e:
        error_msg = "Invalid input chat_request. Error: {}".format(str(e))
        raise HTTPException(status_code=400, detail=error_msg)

    return EventSourceResponse(async_sse_response_format(chat_event_generator(chat_request)),
                               ping_message_factory=lambda: ServerSentEvent(**IGNORE_PING_COMMENT))


@complete_chat_router.post("/complete")
async def complete(request: Request):
    body_str = await request.body()

    try:
        chat_request = ChatCompleteRequest.parse_raw(body_str)
        logger.info("Got chat request: {}".format(chat_request))
    except ValidationError as e:
        error_msg = "Invalid input chat_request. Error: {}".format(str(e))
        raise HTTPException(status_code=400, detail=error_msg)

    response_items = await chat_event_response(chat_request)

    return json_response_format(response_items)


@complete_chat_router.get("/heartbeat")
async def heartbeat(chat_id: str = None, session_id: str = None):
    if not chat_id and not session_id:
        raise HTTPException(status_code=400, detail="Either chat_id or session_id must be provided.")

    input_chat_id = chat_id or session_id

    conversation = await ConversationDAO.get_conversation(input_chat_id)
    if not conversation:
        logger.info(f'Call heartbeat on a non-exist conversion, {input_chat_id}')
        return json_response_format("conversation is not created, skip")

    if conversation.sandbox_id is None:
        logger.error(f'No sandbox id for heartbeat, chat id {input_chat_id}')
        raise HTTPException(status_code=404, detail=f'No sandbox id for heartbeat, chat id {input_chat_id}')

    # TODO Add exception handling logic here for heartbeat failed in sandbox side
    heartbeat_response = await AsyncSandboxClient(conversation.sandbox_id).heartbeat()
    logger.info(f"Heartbeat response {heartbeat_response}")

    return json_response_format("succeed")
