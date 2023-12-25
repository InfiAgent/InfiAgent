from typing import Union, Dict
from werkzeug.datastructures import FileStorage
from ...tools.base_tool import BaseTool
from ...utils import clean_ansi, get_logger
from jupyter_client import BlockingKernelClient
import json
import os
import queue
import re
import subprocess
import sys
import time
import traceback
from enum import Enum
from ...utils.file_utils import clear_files

logger = get_logger()

root_directory = os.path.abspath(__file__)
while 'infiagent' not in os.path.basename(root_directory):
    root_directory = os.path.dirname(root_directory)

WORK_DIR = f'{root_directory}/tmp/ci_workspace'
FILE_DIR = f'{root_directory}/tmp/upload_files'


class _Type(Enum):
    SUCCESS = 1
    ERROR = 2
    FAIL = 3


class PythonSandBoxToolResponse:

    def __init__(self,
                 sand_box_response: str,
                 _type: _Type) -> None:
        self._sand_box_response = sand_box_response
        self._type = _type

    @property
    def output_text(self):
        return self._format(self._sand_box_response, self._type)

    @property
    def raw_output(self):
        return self._sand_box_response

    @classmethod
    def _format(cls, sandbox_response, _type):
        if _type == _Type.FAIL:
            msg = f"\nCode execution error\n"
            msg += f"What happened: {sandbox_response}"
        else:
            msg = ""
            if _type == _Type.SUCCESS:
                msg += "\nSTDOUT:\n"
                msg += f"```python\n{clean_ansi(sandbox_response)}\n```" + "\n"
            elif _type == _Type.ERROR:
                msg += "\nSTDERR:\n"
                msg += f"```python\n{clean_ansi(sandbox_response)}\n```" + "\n"
        return msg


class AsyncPythonSandBoxTool(BaseTool):
    _KERNEL_CLIENTS: Dict[int, BlockingKernelClient] = {}
    LAUNCH_KERNEL_PY = (f"import os\nos.chdir('{root_directory}/tmp')\nfrom ipykernel import kernelapp as "
                        f"app\napp.launch_new_instance()")

    def __init__(self, name, description, **kwargs):
        super().__init__(name, description, **kwargs)
        self._sandbox_id = None

    @classmethod
    async def create(cls, config_data, **params):
        # Unpack the config_data dictionary and any additional parameters
        instance = cls(name=config_data['name'], description=config_data['description'], **params)
        return instance

    @classmethod
    def kill_kernels(cls, sandbox_id):
        if sandbox_id in AsyncPythonSandBoxTool._KERNEL_CLIENTS:
            AsyncPythonSandBoxTool._KERNEL_CLIENTS[sandbox_id].shutdown()
            del AsyncPythonSandBoxTool._KERNEL_CLIENTS[sandbox_id]
        clear_files(os.path.join(WORK_DIR, sandbox_id))
        clear_files(os.path.join(FILE_DIR, sandbox_id))

    def _start_kernel(self) -> BlockingKernelClient:
        connection_file = os.path.join(WORK_DIR, self.sandbox_id, f'kernel_connection_file_{self.sandbox_id}.json')
        launch_kernel_script = os.path.join(WORK_DIR, self.sandbox_id, f'launch_kernel_{self.sandbox_id}.py')
        for f in [connection_file, launch_kernel_script]:
            if os.path.exists(f):
                os.remove(f)

        os.makedirs(os.path.join(WORK_DIR, self.sandbox_id), exist_ok=True)
        with open(launch_kernel_script, 'w') as fout:
            fout.write(AsyncPythonSandBoxTool.LAUNCH_KERNEL_PY)

        kernel_process = subprocess.Popen([
            sys.executable,
            launch_kernel_script,
            '--IPKernelApp.connection_file',
            connection_file,
            '--matplotlib=inline',
            '--quiet',
        ],
            cwd=WORK_DIR)

        # Wait for kernel connection file to be written
        while True:
            if not os.path.isfile(connection_file):
                time.sleep(0.1)
            else:
                # Keep looping if JSON parsing fails, file may be partially written
                try:
                    with open(connection_file, 'r') as fp:
                        json.load(fp)
                    break
                except json.JSONDecodeError:
                    pass

        # Client
        kc = BlockingKernelClient(connection_file=connection_file)
        kc.load_connection_file()
        kc.start_channels()
        kc.wait_for_ready()
        return kc

    async def set_sandbox_id(self, sandbox_id):
        self._sandbox_id = sandbox_id

    @property
    def sandbox_id(self):
        """Getter for sandbox_id."""
        return self._sandbox_id

    async def sync_to_sandbox(self, file: Union[str, Dict, FileStorage]) -> str:
        return os.path.join(root_directory, f"tmp/upload_files/{self.sandbox_id}/{file.split('/')[-1]}")

    @staticmethod
    def _input_handler(input_code: str) -> str:
        # 使用正则表达式查找被三重反引号包围的代码块
        code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', input_code, re.DOTALL)

        # 合并所有找到的代码块
        python_code_cleaned = '\n'.join(code_blocks).strip()

        return python_code_cleaned

    @staticmethod
    def _escape_ansi(line: str) -> str:
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', line)

    @staticmethod
    def _execute_code(kc: BlockingKernelClient, code: str) -> PythonSandBoxToolResponse:
        kc.wait_for_ready()
        kc.execute(code)
        result = []
        state = _Type.FAIL

        while True:
            finished = False
            try:
                msg = kc.get_iopub_msg()
                msg_type = msg['msg_type']
                logger.info(msg_type)
                if msg_type == 'status':
                    if msg['content'].get('execution_state') == 'idle':
                        finished = True
                elif msg_type == 'execute_result':
                    text = msg['content']['data'].get('text/plain', '')
                    result.append(text)
                    state = _Type.SUCCESS
                elif msg_type == 'stream':
                    text = msg['content']['text']
                    result.append(text)
                    state = _Type.SUCCESS
                elif msg_type == 'error':
                    text = AsyncPythonSandBoxTool._escape_ansi('\n'.join(msg['content']['traceback']))
                    result.append(text)
                    state = _Type.ERROR
            except queue.Empty:
                text = 'Timeout: Code execution exceeded the time limit.'
                result.append(text)
                state = _Type.FAIL
                finished = True
            except Exception:
                text = 'The code interpreter encountered an unexpected error.'
                result.append(text)
                logger.error(''.join(traceback.format_exception(*sys.exc_info())))
                state = _Type.FAIL
                finished = True
            if finished:
                break
        output = '\n'.join(result)
        return PythonSandBoxToolResponse(sand_box_response=output, _type=state)

    async def async_run(self, req: str):
        formatted_input = self._input_handler(req)
        if self.sandbox_id in AsyncPythonSandBoxTool._KERNEL_CLIENTS:
            kc = AsyncPythonSandBoxTool._KERNEL_CLIENTS[self.sandbox_id]
        else:
            kc = self._start_kernel()
            AsyncPythonSandBoxTool._KERNEL_CLIENTS[self.sandbox_id] = kc

        return self._execute_code(kc, formatted_input)


