import os
import re
import argparse
import asyncio
import logging
import sys
import json
import io

import openai


import infiagent
from infiagent.utils import get_logger, upload_files, get_file_name_and_path
from infiagent.services.chat_complete_service import predict


logger = get_logger()


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

        parser.add_argument('--config_path',
                            help='Config path for demo',
                            default="configs/agent_configs/react_agent_llama_async.yaml",
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

def read_dicts_from_file(file_name):
    """
    Read a file with each line containing a JSON string representing a dictionary,
    and return a list of dictionaries.

    :param file_name: Name of the file to read from.
    :return: List of dictionaries.
    """
    dict_list = []
    with open(file_name, 'r') as file:
        for line in file:
            # Convert the JSON string back to a dictionary.
            dictionary = json.loads(line.rstrip('\n'))
            dict_list.append(dictionary)
    return dict_list

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
    extracted_data = read_dicts_from_file('./data/da-dev-questions.jsonl')
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
                raise ValueError("OPENAI_API_KEY is None, please provide open ai key to use open ai model. Adding "
                                 "'--api_key' to set it up")

        # 获取 'openai' 的 logger
        openai_logger = logging.getLogger('openai')
        # 设置日志级别为 'WARNING'，这样 'INFO' 级别的日志就不会被打印了
        openai_logger.setLevel(logging.WARNING)
    else:
        logger.info("use local model ")

    table_path = 'data/da-dev-tables'
    results = []

    i = 1
    for q in extracted_data:
        input_text = q['question']
        concepts = q['concepts']
        file_path = q['file_name']
        constraints = q['constraints']
        format = q['format']

        file_path = os.path.join(table_path, file_path)

        print(f'input_text: {input_text}')
        print(f'concepts: {concepts}')
        print(f'file_path: {file_path}')

        uploaded_file = UploadedFile(file_path)
        print(uploaded_file)

        prompt = f"Question: {input_text}\n{constraints}\n"

        response = await predict(
            prompt=prompt,
            model_name=model_name,
            config_path=args.config_path,
            uploaded_files=[uploaded_file]
        )

        iteration_result = {
            'id': q['id'],
            'input_text': prompt,
            'concepts': concepts,
            'file_path': file_path,
            'response': response,
            'format': format
        }
        results.append(iteration_result)
        print(f"response: {response}")

        if i % 10 == 0:
            with open('results_{}.json'.format(model_name), 'w') as outfile:
                json.dump(results, outfile, indent=4)

        i += 1

    with open('results_{}.json'.format(model_name), 'w') as outfile:
        json.dump(results, outfile, indent=4)


if __name__ == '__main__':
    asyncio.run(main())
    # main()


