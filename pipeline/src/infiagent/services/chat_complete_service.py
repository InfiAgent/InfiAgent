import time
from io import BytesIO
from typing import Any, Dict, List, Union

from fastapi import UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile
from werkzeug.datastructures import FileStorage

from ..conversation_sessions import CodeInterpreterSession
from ..exceptions.exceptions import (
    DependencyException,
    InputErrorException,
    InternalErrorException,
    ModelMaxIterationsException,
)
from ..schemas import Message, RoleType
from ..utils import get_logger
from ..tools import AsyncPythonSandBoxTool

logger = get_logger()


async def predict(
        prompt: str,
        model_name: str,
        config_path: str,
        uploaded_files: Any,
        **kwargs: Dict[str, Any]):
    start_time = time.time()

    # create new session
    session = await CodeInterpreterSession.create(
        model_name=model_name,
        config_path=config_path,
        **kwargs
    )

    files = upload_files(uploaded_files, session.session_id)
    logger.info(f"Session Creation Latency: {time.time() - start_time}")

    # upload file
    if isinstance(files, str):
        logger.info(f"Upload {files} as file path")
        await session.upload_to_sandbox(files)
    # upload list of file
    elif isinstance(files, list):
        for file in files:
            if isinstance(file, str):
                await session.upload_to_sandbox(file)
            elif isinstance(file, UploadFile) or isinstance(file, StarletteUploadFile):
                file_content = file.file.read()  # get file content
                file_like_object = BytesIO(file_content)
                file_storage = FileStorage(
                    stream=file_like_object,
                    filename=file.filename,
                    content_type=file.content_type
                )
                await session.upload_to_sandbox(file_storage)
            else:
                raise InputErrorException("The file type {} not supported, can't be uploaded".format(type(file)))

    # chat
    try:
        logger.info(f"Instruction message: {prompt}")
        content = None
        output_files = []
        user_messages = [Message(RoleType.User, prompt)]
        async for response in session.chat(user_messages):
            logger.info(f'Session Chat Response: {response}')
            if content is None:
                content = response.output_text
            else:
                content += response.output_text

            output_files.extend([output_file.__dict__() for output_file in response.output_files])

        session.messages.append(Message(RoleType.Agent, content))
        AsyncPythonSandBoxTool.kill_kernels(session.session_id)
        logger.info(f"Release python sandbox {session.session_id}")
        logger.info(f"Total Latency: {time.time() - start_time}")

        return content

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
        
        raise Exception(err_msg)

import time
from typing import Union, List, Any, Dict
from io import BytesIO

from fastapi import UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile

from ..conversation_sessions import CodeInterpreterSession
from ..schemas import (
    Message,
    RoleType
)
from werkzeug.datastructures import FileStorage

from ..exceptions.exceptions import InputErrorException, DependencyException, InternalErrorException, \
    ModelMaxIterationsException

from ..utils import get_logger, upload_files

logger = get_logger()


async def predict(
        prompt: str,
        model_name: str,
        uploaded_files: Any,
        **kwargs: Dict[str, Any]):
    start_time = time.time()

    # create new session
    session = await CodeInterpreterSession.create(
        model_name=model_name,
        **kwargs
    )

    files = upload_files(uploaded_files, session.session_id)
    logger.info(f"Session Creation Latency: {time.time() - start_time}")

    # upload file
    if isinstance(files, str):
        logger.info(f"Upload {files} as file path")
        await session.upload_to_sandbox(files)
    # upload list of file
    elif isinstance(files, list):
        for file in files:
            if isinstance(file, str):
                await session.upload_to_sandbox(file)
            elif isinstance(file, UploadFile) or isinstance(file, StarletteUploadFile):
                file_content = file.file.read()  # get file content
                file_like_object = BytesIO(file_content)
                file_storage = FileStorage(
                    stream=file_like_object,
                    filename=file.filename,
                    content_type=file.content_type
                )
                await session.upload_to_sandbox(file_storage)
            else:
                raise InputErrorException("The file type {} not supported, can't be uploaded".format(type(file)))

    # chat
    try:
        logger.info(f"Instruction message: {prompt}")
        content = None
        output_files = []
        user_messages = [Message(RoleType.User, prompt)]

        async for response in session.chat(user_messages):
            logger.info(f'Session Chat Response: {response}')
            if content is None:
                content = response.output_text
            else:
                content += response.output_text

            output_files.extend([output_file.__dict__() for output_file in response.output_files])

        session.messages.append(Message(RoleType.Agent, content))

        logger.info(f"Total Latency: {time.time() - start_time}")

        return content
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
        
        raise Exception(err_msg)
