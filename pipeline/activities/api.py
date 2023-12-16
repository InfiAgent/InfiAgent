import asyncio
import uuid

import uvloop
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from starlette.responses import JSONResponse, Response

from .activity_helpers import DONE
from .complete_chat import complete_chat_router
from .predict import predict_router

try:
    import infiagent
    from infiagent.schemas import FailedResponseBaseData
    from infiagent.utils import get_logger, init_logging, log_id_var
except ImportError:
    print("import infiagent failed, please install infiagent by 'pip install .' in the pipeline directory of ADA-Agent")
    from ..schemas import FailedResponseBaseData
    from ..utils import get_logger, init_logging, log_id_var

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

SSE_API_PATHS = ["/complete_sse"]
LOG_ID_HEADER_NAME = "X-Tt-Logid"


load_dotenv()
init_logging()
logger = get_logger()

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(complete_chat_router)
app.include_router(predict_router)


@app.middleware("http")
async def log_id_middleware(request: Request, call_next):
    # Get X-Tt-Logid from request headers
    log_id = request.headers.get(LOG_ID_HEADER_NAME)
    if not log_id:
        # Generate a log_id if not present in headers
        log_id = str(uuid.uuid4())

    log_id_var.set(log_id)

    response: Response = await call_next(request)
    response.headers[LOG_ID_HEADER_NAME] = log_id_var.get()
    return response


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_msg = "Failed to handle request. Internal Server error: {}".format(str(exc))
    logger.error(error_msg, exc_info=True)

    if request.url.path in SSE_API_PATHS:
        return EventSourceResponse(ServerSentEvent(data=DONE))
    else:
        return JSONResponse(
            status_code=500,
            content={
                "response": error_msg,
                "ResponseBase": FailedResponseBaseData().dict()
            }
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_msg = "Failed to handle request. Error: {}".format(exc.detail)
    logger.error(error_msg, exc_info=True)

    if request.url.path in SSE_API_PATHS:
        return EventSourceResponse(ServerSentEvent(data=DONE))
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "response": error_msg,
                "ResponseBase": FailedResponseBaseData().dict()
            }
        )
