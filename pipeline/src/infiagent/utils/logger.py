
# Custom Logger Adapter to include X-Tt-Logid
import logging
from contextvars import ContextVar


log_id_var: ContextVar[str] = ContextVar("log_id", default="")


class ContextualLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        log_id = log_id_var.get()
        return f"[{log_id}] : {msg}", kwargs


def init_logging():
    """
    Initialize logging configuration.
    """
    # Basic logging configuration with your specified settings
    # config_default()
    openai_logger = logging.getLogger("openai")
    openai_logger.setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.INFO,
        datefmt=r'%Y/%m/%d %H:%M:%S',
        format=r'[%(levelname)s %(asctime)s %(filename)s:%(lineno)d] %(message)s',
    )


def get_logger() -> logging.LoggerAdapter:
    """
    Retrieve a logger instance configured with X-Tt-Logid.
    """
    logger = logging.getLogger("infiagent_logger")
    logger.setLevel(logging.INFO)
    return ContextualLoggerAdapter(logger, {})
