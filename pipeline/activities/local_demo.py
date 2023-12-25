import argparse
import asyncio
import logging
import os
import sys

import streamlit as st  # type: ignore
import uvloop
import openai

try:
    import infiagent
    from infiagent.utils import get_logger, upload_files
    from infiagent.services.chat_complete_service import predict
except ImportError:
    raise (
        "import infiagent failed, please install infiagent by 'pip install -e .' in the pipeline directory of ADA-Agent")

logger = get_logger()

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def _get_script_params():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--llm',
                            help='LLM Model for demo',
                            required=False, type=str)
        parser.add_argument('--api_key',
                            help='Open API token key.',
                            required=False, type=str)
        parser.add_argument('--config_path',
                            help='Config path for demo',
                            # default="configs/agent_configs/react_agent_gpt4_async.yaml",
                            required=False, type=str)

        args = parser.parse_args()

        return args
    except Exception as e:
        logger.error("Failed to get script input arguments: {}".format(str(e)), exc_info=True)

    return None


async def main():
    args = _get_script_params()

    model_name = getattr(args, "llm", None)
    open_ai_key = getattr(args, "api_key", None)
    config_path = getattr(args, "config_path", None)

    if "OPEN_AI" in model_name:
        logger.info("setup open ai ")
        if os.environ.get("OPENAI_API_KEY") is None:
            if open_ai_key:
                openai.api_key = open_ai_key
                os.environ["OPENAI_API_KEY"] = open_ai_key
            else:
                raise ValueError(
                    "OPENAI_API_KEY is None, please provide opekn ai key to use open ai model. Adding '--api_key' to set it up")

        # 获取 'openai' 的 logger
        openai_logger = logging.getLogger('openai')
        # 设置日志级别为 'WARNING'，这样 'INFO' 级别的日志就不会被打印了
        openai_logger.setLevel(logging.WARNING)

    else:
        logger.info("use local model ")

    st.set_page_config(layout="centered")

    st.title("InfiAgent Code Interpreter Demo 🚀")

    # Initialize session state variables if not already present
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # UI components
    input_text = st.text_area("Write your prompt")
    uploaded_files = st.file_uploader("Upload your files", accept_multiple_files=True)
    button_pressed = st.button("Run code interpreter", use_container_width=True)

    # When button is pressed
    if button_pressed and input_text != "":
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "message": input_text})

        # Predict response (assuming you have the necessary async handling)
        response = await predict(
            prompt=input_text,
            model_name=model_name,
            config_path=config_path,
            uploaded_files=uploaded_files,
        )

        # Add assistant message to chat history
        st.session_state.chat_history.append({"role": "assistant", "message": response})

    # Display chat history
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.write(chat["message"])


if __name__ == "__main__":
    asyncio.run(main())
