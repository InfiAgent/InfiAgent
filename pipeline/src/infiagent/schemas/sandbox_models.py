from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel

class SandboxStatus(Enum):
    """
    Enumerated type for agent types.
    """
    success = "success"
    failed = "failed"
    timeout = "timeout"

class CodeOutput(BaseModel):
    type: str
    content: str

class ReturnedFile(BaseModel):
    download_link: str
    name: str
    path: str

class CodeRunResult(BaseModel):
    code_output_result: List[CodeOutput]
    deleted_files: List[ReturnedFile]
    new_generated_files: List[ReturnedFile]

class CodeRunData(BaseModel):
    is_partial: bool
    result: CodeRunResult


class RunCodeOutput(BaseModel):
    code: int
    message: str
    data: Optional[CodeRunData]

class CreateSessionOutput(BaseModel):
    code: int
    message: str


class ErrorResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any]


class UploadOutput(BaseModel):
    code: int
    message: Optional[str]
    data: Optional[str]


# Model for successful response (assuming it's a text file for this example)
class DownloadSuccessOutput(BaseModel):
    file_name: str  # this is not part of server response. We must fill this field in client.
    content: str


class HeartbeatOutput(BaseModel):
    code: Optional[int]
    message: Optional[str]


class RefreshSandboxOutput(BaseModel):
    code: Optional[int]
    message: Optional[str]


