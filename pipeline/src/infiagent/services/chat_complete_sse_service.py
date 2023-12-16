import time

from ..activities.activity_helpers import DONE
from ..conversation_sessions import CodeInterpreterStreamSession
from ..db.conversation_dao import ConversationDAO
from ..db.conversation_do import ConversationDO, ConversationStatus
from ..exceptions.exceptions import (
    DependencyException,
    InputErrorException,
    InternalErrorException,
    ModelMaxIterationsException,
)
from ..schemas import (
    FINISH_STATUS,
    PROCESSING_STATUS,
    ChatCompleteRequest,
    MediaFile,
    Message,
    RoleType,
    chat_request_to_response,
    create_empty_response,
    update_chat_response_with_message,
)
from ..utils import get_logger
from ..utils.file_utils import get_file_name_and_path

EMPTY_RESPONSE = create_empty_response()

logger = get_logger()


async def chat_event_generator(chat_request: ChatCompleteRequest):
    """
    Init a chat session and start pushing response back.
    This function is for SSE apis
    """
    base_response = EMPTY_RESPONSE
    session = None
    start_time = time.time()
    try:
        base_response = chat_request_to_response(chat_request)

        logger.info("Start processing chat {} for {}, using model {}".format(chat_request.chat_id, chat_request.user,
                                                                             chat_request.model))
        # init
        # 1. get or create conversation in DB (not add current chat message yet)
        # 2. init chat session
        conversation = await get_or_create_conversation(chat_request)

        session = await CodeInterpreterStreamSession.create(model_name=chat_request.model, conversation=conversation)

        user_messages = [Message(RoleType.User, message["content"]) for message in chat_request.messages]
        input_files = _get_input_file(chat_request)

        # yield chat response piece by piece
        async for chat_response in process_chat_response(session, base_response, user_messages, input_files):
            yield chat_response
    except (ModelMaxIterationsException, DependencyException, InputErrorException, InternalErrorException, Exception) \
            as e:
        exception_messages = {
            ModelMaxIterationsException: "Sorry. The agent didn't find the correct answer after multiple trials, "
                                         "Please try another question.",
            DependencyException: "Agent failed to process message due to dependency issue. You can try it later. "
                                 "If it still happens, please contact oncall.",
            InputErrorException: "Agent failed to process message due to value issue. If you believe all input are "
                                 "correct, please contact oncall.",
            InternalErrorException: "Agent failed to process message due to internal error, please contact oncall.",
            Exception: "Agent failed to process message due to unknown error, please contact oncall."
        }

        err_msg = exception_messages.get(type(e), f"Unknown error occurred: {str(e)}")
        logger.error(err_msg, exc_info=True)
        message = Message(role=RoleType.System, content=err_msg)
        yield update_chat_response_with_message(base_response.copy(), message, status=FINISH_STATUS).dict()
        if session and session.conversation:
            session.conversation.status = ConversationStatus.FAILED

    yield DONE

    if session and session.conversation:
        await ConversationDAO.update_conversation(session.conversation)


async def chat_event_response(chat_request: ChatCompleteRequest):
    """
    Init a chat session and collect all response and return.
    This function will collect all response and return
    """

    base_response = chat_request_to_response(chat_request)

    logger.info("Start processing chat {} for {}, using model {}".format(chat_request.chat_id, chat_request.user,
                                                                         chat_request.model))

    conversation = await get_or_create_conversation(chat_request)

    start_time = time.time()
    session = await CodeInterpreterStreamSession.create(model_name=chat_request.model, conversation=conversation)
    session_created_time = time.time()

    user_messages = [Message(RoleType.User, message["content"]) for message in chat_request.messages]
    input_files = _get_input_file(chat_request)

    try:
        content = None
        output_files = []
        async for response in session.chat(user_messages, input_files):
            if content is None:
                content = response.output_text
            else:
                content += response.output_text

            output_files.extend([output_file.__dict__() for output_file in response.output_files])

        message = Message(role=RoleType.Agent, content=content)

        return update_chat_response_with_message(base_response.copy(), message).dict()
    except (ModelMaxIterationsException, DependencyException, InputErrorException, InternalErrorException, Exception) \
            as e:
        exception_messages = {
            ModelMaxIterationsException: "Sorry. The agent didn't find the correct answer after multiple trials, "
                                         "Please try another question.",
            DependencyException: "Agent failed to process message due to dependency issue. You can try it later. "
                                 "If it still happens, please contact oncall.",
            InputErrorException: "Agent failed to process message due to value issue. If you believe all input are "
                                 "correct, please contact oncall.",
            InternalErrorException: "Agent failed to process message due to internal error, please contact oncall.",
            Exception: "Agent failed to process message due to unknown error, please contact oncall."
        }
        err_msg = exception_messages.get(type(e), f"Unknown error occurred: {str(e)}")
        logger.error(err_msg, exc_info=True)
        if session and session.conversation:
            session.conversation.status = ConversationStatus.FAILED
        await ConversationDAO.update_conversation(session.conversation)
        raise Exception(err_msg) from e


async def get_or_create_conversation(chat_request: ChatCompleteRequest):
    """
    get conversation data from db or create new conversation based on input and store updated in DB
    """
    chat_id = chat_request.chat_id
    if not chat_request.chat_id:
        raise InputErrorException("Invalid chat ID.")

    # Check if conversation exists in db
    conversation_data = await ConversationDAO.get_conversation(chat_id)

    if not conversation_data:
        logger.info("No existing conversation for {}. Creating new conversation.".format(chat_id))
        conversation_data = ConversationDO.create_conversation_from_request(chat_request)
        await ConversationDAO.add_conversation(conversation_data)
    else:
        # TODO: Add status management, change status after fail then user can re-run, then reject request while
        #  another session is updating the conversation
        if conversation_data.is_in_running_status():
            logger.warning("Conversation {} is still running, should aborting new changes")

        logger.info("Got existing conversation {}, starting session.".format(chat_id))
        # update current info into existing conversation
        conversation_data = conversation_data.update_from_chat_request(chat_request)
        await ConversationDAO.update_conversation(conversation_data)

    return conversation_data


async def process_chat_response(session, base_response, user_messages, input_files=[]):
    """
    Receive chat response, update the message and status. This function will mark step status to be RUNNING and last
    response status to be FINISH
    """
    async_chat_generator = session.chat(user_messages, input_files)
    chat_response_buffer = None

    async for chat_response in async_chat_generator:
        if chat_response_buffer:
            # Not the last one, using processing
            yield await update_chat_response(chat_response_buffer, base_response, PROCESSING_STATUS)
        chat_response_buffer = chat_response

    if chat_response_buffer:
        # the last one, using finish
        yield await update_chat_response(chat_response_buffer, base_response, FINISH_STATUS)


async def update_chat_response(chat_response, base_response, status):
    logger.info(f'Update Session Chat Response to conversation.')
    message = Message(role=RoleType.Agent, content=chat_response.output_text)

    return update_chat_response_with_message(base_response.copy(), message, status=status).dict()


def _get_input_file(chat_request: ChatCompleteRequest):
    input_files = []
    if chat_request.code_interpreter and "tos_key" in chat_request.code_interpreter:
        input_file = chat_request.code_interpreter["tos_key"]
        file_name, tos_path = get_file_name_and_path(input_file)
        input_file = MediaFile(file_name=file_name, tos_path=tos_path)
        input_files.append(input_file.__dict__())
    return input_files
