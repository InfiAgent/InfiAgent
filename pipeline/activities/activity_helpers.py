import json

from sse_starlette import ServerSentEvent

from infiagent.schemas import ResponseBaseData


IGNORE_PING_COMMENT = {"comment": "IGNORE PING"}
DONE = "[DONE]"


async def async_sse_response_format(response_data_gen):
    async for content in response_data_gen:
        if content == DONE:
            sse_event = ServerSentEvent(data=DONE)
        else:
            data_dict = {
                "response": content,
                "ResponseBase": ResponseBaseData().dict()
            }
            sse_event = ServerSentEvent(data=json.dumps(data_dict, ensure_ascii=False))
        yield sse_event


def json_response_format(content):
    return {
        "response": content,
        "ResponseBase": ResponseBaseData().dict()
    }


def get_ignore_ping_comment():
    return lambda: ServerSentEvent(**IGNORE_PING_COMMENT)
