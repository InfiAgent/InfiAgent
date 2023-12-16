# coding: utf-8
from pydantic import BaseModel


class ResponseBaseData(BaseModel):
    code: int = 0
    message: str = "success"


class FailedResponseBaseData(BaseModel):
    code: int = 0
    message: str = "failed"
