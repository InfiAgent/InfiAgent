import os
import re
import argparse
import asyncio
import logging
import sys
import json

import uvloop
import openai
try:
    import infiagent
    from infiagent.utils import get_logger, upload_files, get_file_name_and_path
    from infiagent.services.chat_complete_service import predict
except ImportError:
    print("import infiagent failed, please install infiagent by 'pip install .' in the pipeline directory of ADA-Agent")
    from ..utils import get_logger, upload_files, get_file_name_and_path
    from ..services.chat_complete_service import predict

logger = get_logger()

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Get the current script's directory
root_directory = os.path.abspath(__file__)

# Loop to find the root directory (with the name "smart_agent")
while 'smart_agent' not in os.path.basename(root_directory):
    root_directory = os.path.dirname(root_directory)

# Add the root directory to the sys path if it is not exist
if root_directory not in sys.path:
    sys.path.append(root_directory)

from ..utils import *

TEMP_FILE_UPLOAD_DIR = "./tmp/upload_files/"

import io

class UploadedFile(io.BytesIO):
    def __init__(self, path):
        with open(path, 'rb') as file:
            data = file.read()

        super().__init__(data)

        self.name = path.split("/")[-1]  # 获取文件名
        self.type = 'application/octet-stream'  # 或者其他适当的 MIME 类型
        self.size = len(data)

    def __repr__(self):
        return f"MyUploadedFile(name={self.name}, size={self.size}, type={self.type})"
    
    def __len__(self):

        return self.size

# # 使用例子
# file_path = "path/to/your/file"
# uploaded_file = MyUploadedFile(file_path)

# print(uploaded_file)


def _get_script_params():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--llm',
                            help='LLM Model for demo',
                            required=False, type=str)
        parser.add_argument('--api_key',
                            help='Open API token key.',
                            required=False, type=str)

        args = parser.parse_args()

        return args
    except Exception as e:
        logger.error("Failed to get script input arguments: {}".format(str(e)), exc_info=True)

    return None


def extract_questions_and_concepts(file_path):
    # Read the content of the text file
    with open(file_path, 'r') as file:
        content = file.read()

    # Use regular expressions to extract questions and concepts
    pattern = r'\\Question{(.*?)}\s*\\Concepts{(.*?)}'
    matches = re.findall(pattern, content, re.DOTALL)

    # Build a list of dictionaries containing the questions and concepts
    data = []
    for match in matches:
        question = match[0].strip()
        concepts = [concept.strip() for concept in match[1].split(',')]
        data.append({
            'question': question,
            'concepts': concepts
        })

    return data

def read_questions(file_path):
    print(file_path)
    with open(file_path) as f:
        questions = json.load(f)
    
    return questions

def extract_data_from_folder(folder_path):

    print(f'folder_path {folder_path}')

    extracted_data = {}

    # Traverse the files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.questions'):  # You can filter files based on their type
            file_path = os.path.join(folder_path, file_name)
            file_data = read_questions(file_path)
            file_name_without_extension = os.path.splitext(file_name)[0]
            extracted_data[file_name_without_extension] = file_data

    return extracted_data


async def main():
# def main():
    folder_path = '/root/data/eval_dataset/questions_v2'  # Replace with your folder path
    extracted_data = extract_data_from_folder(folder_path)
    
    args = _get_script_params()

    model_name = getattr(args, "llm", None)

    open_ai_key = getattr(args, "api_key", None)

    if "OPEN_AI" in model_name:
        logger.info("setup open ai ")
        if os.environ.get("OPENAI_API_KEY") is None:
            if open_ai_key:
                openai.api_key = open_ai_key
                os.environ["OPENAI_API_KEY"] = open_ai_key
            else:
                raise ValueError("OPENAI_API_KEY is None, please provide opekn ai key to use open ai model. Adding '--api_key' to set it up")

        # 获取 'openai' 的 logger
        openai_logger = logging.getLogger('openai')
        # 设置日志级别为 'WARNING'，这样 'INFO' 级别的日志就不会被打印了
        openai_logger.setLevel(logging.WARNING)

    else:
        logger.info("use local model ")

    tabel_path = '/root/data/eval_dataset/tables_v2'
    for k,v in extracted_data.items():
        for q in v:
            input_text = q['question']
            concepts = q['concepts']
            file_path = q['file_name']

            file_path = os.path.join(tabel_path, file_path)

            print(f'input_text: {input_text}')
            print(f'concepts: {concepts}')
            print(f'file_path: {file_path}')
            

            uploaded_file = UploadedFile(file_path)

            print(uploaded_file)

            response = await predict(
                prompt=input_text,
                model_name=model_name,
                uploaded_files=[uploaded_file]
            )

            print(f"response: {response}")

            break

if __name__ == '__main__':
    asyncio.run(main())
    # main()


