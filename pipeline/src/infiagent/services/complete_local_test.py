import asyncio

from ..schemas import Message, RoleType
from ..schemas import chat_request_to_response, ChatCompleteRequest, update_chat_response_with_message

DONE = "DONE"

FINISH_STATUS = "FINISH"
FAILED_STATUS = "FAILED"
PROCESSING_STATUS = "PROCESSING"


def message_generator(messages):
    for message in messages:
        yield message


def update_chat_status_local(async_chat_generator):
    """Yields pairs (current_item, is_last) for each item in async_gen."""
    buffered_chat = None
    for item in async_chat_generator:
        if buffered_chat is not None:
            yield buffered_chat, False
        buffered_chat = item
    if buffered_chat is not None:
        yield buffered_chat, True


async def chat_local_event_generator(chat_request: ChatCompleteRequest):
    """
    Init a chat session and start pushing response back
    """
    message1 = Message(role=RoleType.User, content="你好，我是豆包")
    message2 = Message(role=RoleType.Agent, content="今天天气很好")
    message3 = Message(role=RoleType.Agent, content="再见")
    messages = [message1, message2, message3]

    base_response = chat_request_to_response(chat_request)
    try:
        for message, is_last in update_chat_status_local(message_generator(messages)):
            status = FINISH_STATUS if is_last else PROCESSING_STATUS
            yield update_chat_response_with_message(base_response.copy(), message, status=status).dict()
            await asyncio.sleep(2)
    except Exception as e:
        failed_message = Message(role=RoleType.System, content="Failed: {}".format(str(e)))
        yield update_chat_response_with_message(base_response.copy(), failed_message, status=FAILED_STATUS).dict()

    yield DONE


async def chat_local_event(chat_request: ChatCompleteRequest):
    """
    Init a chat session and start pushing response back
    """
    message = Message(role=RoleType.User, content="Hi")

    base_response = chat_request_to_response(chat_request)
    return update_chat_response_with_message(base_response.copy(), message).dict()
