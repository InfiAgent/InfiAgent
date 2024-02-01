import os
import pathlib
from typing import Tuple, Optional, IO, Union, Dict
import time
from hashlib import md5
import docker
from ..tools.base_tool import BaseTool, BaseToolRequest, BaseToolResponse
import re
from ..exceptions.exceptions import InputErrorException, SandBoxFileUploadException
from werkzeug.datastructures import FileStorage
from ..utils import get_logger

logger = get_logger()

try:
    import docker
except ImportError:
    docker = None

WORKING_DIR = os.path.join(os.getcwd(), "tmp/code_space")
OUTPUT_DIR = os.path.join(os.getcwd(), "tmp/output_space")
UPLOAD_PATH = os.path.join(os.getcwd(), "tmp/upload_files")


class CodeToolRequest(BaseToolRequest):
    """
    Request for Code Tool
    """
    def __init__(self, code_str: str):
        # code_str = 'import pandas as pd\nimport numpy as np\n'+ code_str
        code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', code_str, re.DOTALL)
        python_code_cleaned = '\n'.join(code_blocks).strip()
        self.code = python_code_cleaned

class PythonSandBoxToolResponseDocker:
    def __init__(self, formatter, raw_output) -> None:
        self.formatter = formatter
        self.raw_output = raw_output

    @property
    def output_text(self):
        return self.formatter.format(self.raw_output)


class CodeToolResponse(BaseToolResponse):
    """
    Response for Code Tool
    """
    def __init__(self, exit_code: int, log: str, output_dir: str):
        self.exit_code = exit_code
        self.log = log
        self.output_dir = output_dir
        self.output_text = log
    
    def to_dict(self):
        return {
            "exit_code": self.exit_code,
            "log": self.log,
            "output_dir": self.output_dir
        }


class CodeTool(BaseTool):
    """
    Code Tool for code execution
    """
    def __init__(self,
                 name: Optional[str] = "Code Tool",
                 description: Optional[str] = "tool for code_exec",
                #  code_tool_id: Optional[str] = "code",
                 image: Optional[str] = "myimg",
                 time_out: Optional[int] = 60,
                 work_dir: Optional[str] = WORKING_DIR,
                 output_dir: Optional[str] = OUTPUT_DIR,
                 **kwargs
                 ):
        super().__init__(name, description, **kwargs)
        self._client = docker.from_env()
        self._image = image
        self._time_out = time_out
        self._work_dir = work_dir
        self._output_dir = output_dir
        self._upload_file_name = None
        self._upload_file_path = None
        self._code_idx = md5(str(time.time()).encode()).digest().hex()
        self._log_len = 0

    @classmethod
    async def create(cls, config_data, **params):
        # Unpack the config_data dictionary and any additional parameters
        instance = cls(name=config_data['name'], description=config_data['description'], **params)
        return instance

    async def set_sandbox_id(self, sandbox_id):
        self._sandbox_id = sandbox_id

    @property
    def sandbox_id(self):
        """Getter for sandbox_id."""
        return self._sandbox_id if self._sandbox_id else None


    async def async_run(self, req: str):
        req = CodeToolRequest(req)
        code = req.code
        if code is None:
            return "No code to execute", 1, ""
        
        # path and file name for python script
        abs_path = pathlib.Path(self._work_dir).absolute()
        code_hash = self._code_idx
        file_name = f"exec_code_{code_hash}.py"
        file_path = os.path.join(self._work_dir, file_name)
        self._file_path = file_path
        file_dir = os.path.dirname(file_path)
        self._file_dir = file_dir
        os.makedirs(file_dir, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        if self._upload_file_name:
            upload_file_path = os.path.join(UPLOAD_PATH, self._upload_file_name)
        
        # write code to file
        with open(file_path, "a", encoding="utf-8") as fout:
            fout.write(code)
        cmd = f'python3 {file_name}'
        
        # create docker container
        start_time = time.time()
        if self._upload_file_name:
            container = self._client.containers.run(
                image=self._image,
                command=cmd,
                detach=True, 
                working_dir="/workspace",
                mem_limit='1024m',
                volumes={abs_path: {'bind': '/workspace','mode': 'rw'},
                        upload_file_path: {'bind': f'/tmp/upload_files/{self._upload_file_name}','mode': 'rw'}},
                )
        else:
            container = self._client.containers.run(
                image=self._image,
                command=cmd,
                detach=True, 
                working_dir="/workspace",
                mem_limit='10m',
                volumes={abs_path: {'bind': '/workspace','mode': 'rw'}},
                )

        # hold for time_out seconds
        while container.status != "exited" and time.time() - start_time < self._time_out:
            container.reload()
        
        # if time out, stop and remove container
        if container.status != "exited":
            container.stop()
            container.remove()
            return "TIMEOUT", 1, ""
        
        # save log to file
        logs = container.logs().decode("utf-8").rstrip()
        with open(os.path.join(file_dir, f'log.txt'), 'w') as log_file:
            log_file.write(logs)
        new_len = len(logs)
        logs = logs[self._log_len:]
        self._log_len = new_len

        exit_code = container.attrs["State"]["ExitCode"]
        container.remove()

        # save files to output space and rmv files in working space
        output_dir = os.path.join(OUTPUT_DIR, f'output_{code_hash}')
        self._output_dir = output_dir
        # os.makedirs(output_dir, exist_ok=True)
        # os.rename(file_path, os.path.join(file_dir, 'exec_code.py'))
        # for f in os.listdir(abs_path):
        #     os.rename(os.path.join(abs_path, f), os.path.join(output_dir, f))
        # os.rmdir(abs_path)

        response = CodeToolResponse(exit_code, logs, output_dir)
        
        return response

    async def sync_to_sandbox(self, file: Union[str, Dict, FileStorage]) -> str:
        if isinstance(file, str):
            logger.info(f"Upload File As FilePath: {file}")
            file_path = await self.upload_file(file)
        else:
            err_msg = f"Invalid file input type. Expected str, FileStorage, or Dict. Got {type(file)}"
            logger.error(err_msg)
            raise InputErrorException(err_msg)
        
        return file_path

    async def upload_file(self, file_path: str):
        file_name = file_path.split("/")[-1]  # Extract the file name from the path
        self._upload_file_path = file_path
        self._upload_file_name = file_name

        return file_path

    async def save_file(self):
        output_dir = self._output_dir
        file_path = self._file_path
        file_dir = self._file_dir
        abs_path = pathlib.Path(self._work_dir).absolute()
        os.makedirs(output_dir, exist_ok=True)
        os.rename(file_path, os.path.join(file_dir, 'exec_code.py'))
        for f in os.listdir(abs_path):
            os.rename(os.path.join(abs_path, f), os.path.join(output_dir, f))
        os.rmdir(abs_path)
