import logging
import time
import json
import argparse
import traceback
import os

import requests

from utils.utils import read_jsonl, write_jsonl


def define_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('--url_file', type=str, default="url.txt")
    parser.add_argument('--api_key_file', type=str, default="api_key.txt")
    parser.add_argument('--questions_file_path', type=str, default="data/da-dev-questions.jsonl")
    parser.add_argument('--responses_file_path', type=str,
                        default="responses/results_agentllm_7b_reformat_for_test.jsonl")
    parser.add_argument('--model', type=str, default="gpt-3.5-turbo-16k")
    parser.add_argument('--max_resp', type=int, default=2048)

    args = parser.parse_args()
    return args


def call(messages, args):
    headers = {
        "Content-Type": "application/json",
        "Authorization": args.api_key
    }

    data = {
        "max_tokens": args.max_resp,
        "model": args.model,
        "temperature": 0,
        "messages": messages,
    }
    while True:
        try:
            response = requests.post(args.url, headers=headers, data=json.dumps(data))
            result = response.json()
            return result
        except Exception as e:
            logging.error(data)
            logging.error(traceback.format_exc())
            time.sleep(10)


demons = """\Format{{
@shapiro_wilk_statistic[test_statistic]
@shapiro_wilk_p_value[p_value]
where "test_statistic" is a number between 0 and 1 representing the Shapiro-Wilk test statistic. Rounding off the answer to two decimal places.
where "p_value" is a number between 0 and 1 representing the p-value from the Shapiro-Wilk test. Rounding off the answer to four decimal places.
}}
\Answer{{
@shapiro_wilk_statistic[0.56]
@shapiro_wilk_p_value[0.0002]   
}}

\Format{{
@total_votes_outliers_num[outlier_num]
where "outlier_num" is an integer representing the number of values considered outliers in the 'total_votes' column.
}}
\Answer{{
@total_votes_outliers[10]   
}}
"""

reformat_template = """You should strictly follow the output requirements in the Format part. Here're some examples: 
{demons}. 
Your answer should contain all the \"@answer_name[answer]\" in the order mentioned, each \"answer\" should be in the range of value as required. 
The format requirements of this question is:
{format}. Please give your answer:"""

if __name__ == "__main__":
    args = define_arguments()
    args.url = open(args.url_file).read().strip()
    args.api_key = open(args.api_key_file).read().strip()
    args.output_file_path = "{basename}_reformat.jsonl".format(
        basename=os.path.splitext(os.path.basename(args.questions_file_path))[0])

    questions = read_jsonl(args.questions_file_path)
    responses = read_jsonl(args.responses_file_path)

    for response in responses:
        for question in questions:
            if question['id'] == response['id']:
                question_description = question['question']
                format = question['format']
                break

        messages = [{"role": "user", "content": question_description}]
        messages.append({"role": "assistant", "content": response['response']})
        messages.append({"role": "user", "content": reformat_template.format(demons=demons, format=format)})
        reformatted_response = call(messages, args)["choices"][0]["message"]["content"]
        response['response'] = reformatted_response

    write_jsonl(responses, args.output_file_path)
