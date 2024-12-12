import json
import os
from abc import ABC
from typing import Callable, List

import openai

from ..base_llm import BaseLLM
from ...schemas import *


class OpenAIGPTClient(BaseLLM, ABC):
    """
    Wrapper class for OpenAI GPT API collections.

    :param model_name: The name of the model to use.
    :type model_name: str
    :param params: The parameters for the model.
    :type params: OpenAIParamModel
    """
    model_name: str
    params: OpenAIParamModel = OpenAIParamModel()

    def __init__(self, **data):
        super().__init__(**data)
        openai.api_key = os.environ.get("OPENAI_API_KEY", "")

    @classmethod
    async def create(cls, config_data):
        return OpenAIGPTClient(**config_data)

    def get_model_name(self) -> str:
        return self.model_name

    def get_model_param(self) -> OpenAIParamModel:
        return self.params

    def completion(self, prompt: str, **kwargs) -> BaseCompletion:
        """
        Completion method for OpenAI GPT API.

        :param prompt: The prompt to use for completion.
        :type prompt: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: BaseCompletion object.
        :rtype: BaseCompletion

        """
        try:
            #TODO any full parameters support
            response = openai.ChatCompletion.create(
                # n=self.params['n'],
                engine=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.params.temperature,
                max_tokens=self.params.max_tokens,
                top_p=self.params.top_p,
                # frequency_penalty=self.params.frequency_penalty,
                # presence_penalty=self.params.presence_penalty,
                **kwargs
            )
            return BaseCompletion(state="success",
                                  content=response.choices[0].message["content"],
                                  prompt_token=response.get("usage", {}).get("prompt_tokens", 0),
                                  completion_token=response.get("usage", {}).get("completion_tokens", 0))
        except Exception as exception:
            print("Exception:", exception)
            return BaseCompletion(state="error", content=exception)

    async def async_completion(self, prompt: str, **kwargs) -> BaseCompletion:
        """
        Async Completion method for OpenAI GPT API.

        :param prompt: The prompt to use for completion.
        :type prompt: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: BaseCompletion object.
        :rtype: BaseCompletion

        """
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.params.temperature,
                max_tokens=self.params.max_tokens,
                top_p=self.params.top_p,
                # frequency_penalty=self.params.frequency_penalty,
                # presence_penalty=self.params.presence_penalty,
                **kwargs
            )
            return BaseCompletion(state="success",
                                  content=response.choices[0].message["content"],
                                  prompt_token=response.get("usage", {}).get("prompt_tokens", 0),
                                  completion_token=response.get("usage", {}).get("completion_tokens", 0))
        except Exception as exception:
            print("Exception:", exception)
            return BaseCompletion(state="error", content=exception)


    def chat_completion(self, message: List[dict]) -> ChatCompletion:
        """
        Chat completion method for OpenAI GPT API.

        :param message: The message to use for completion.
        :type message: List[dict]
        :return: ChatCompletion object.
        :rtype: ChatCompletion
        """
        try:
            response = openai.ChatCompletion.create(
                n=self.params.n,
                model=self.model_name,
                messages=message,
                temperature=self.params.temperature,
                max_tokens=self.params.max_tokens,
                top_p=self.params.top_p,
                frequency_penalty=self.params.frequency_penalty,
                presence_penalty=self.params.presence_penalty,
            )
            return ChatCompletion(state="success",
                                  role=response.choices[0].message["role"],
                                  content=response.choices[0].message["content"],
                                  prompt_token=response.get("usage", {}).get("prompt_tokens", 0),
                                  completion_token=response.get("usage", {}).get("completion_tokens", 0))
        except Exception as exception:
            print("Exception:", exception)
            return ChatCompletion(state="error", content=exception)

    def stream_chat_completion(self, message: List[dict],  **kwargs):
        """
        Stream output chat completion for OpenAI GPT API.

        :param message: The message (scratchpad) to use for completion. Usually contains json of role and content.
        :type message: List[dict]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: ChatCompletion object.
        :rtype: ChatCompletion
        """
        try:
            response = openai.ChatCompletion.create(
                n=self.params.n,
                model=self.model_name,
                messages=message,
                temperature=self.params.temperature,
                max_tokens=self.params.max_tokens,
                top_p=self.params.top_p,
                frequency_penalty=self.params.frequency_penalty,
                presence_penalty=self.params.presence_penalty,
                stream=True,
                **kwargs
            )
            role = next(response).choices[0].delta["role"]
            messages = []
            ## TODO: Calculate prompt_token and for stream mode
            for resp in response:
                messages.append(resp.choices[0].delta.get("content", ""))
                yield ChatCompletion(state="success",
                                     role=role,
                                     content=messages[-1],
                                     prompt_token=0,
                                     completion_token=0)
        except Exception as exception:
            print("Exception:", exception)
            return ChatCompletion(state="error", content=exception)

    def function_chat_completion(self, message: List[dict],
                                 function_map: Dict[str, Callable],
                                 function_schema: List[Dict]) -> ChatCompletionWithHistory:
        """
        Chat completion method for OpenAI GPT API.

        :param message: The message to use for completion.
        :type message: List[dict]
        :param function_map: The function map to use for completion.
        :type function_map: Dict[str, Callable]
        :param function_schema: The function schema to use for completion.
        :type function_schema: List[Dict]
        :return: ChatCompletionWithHistory object.
        :rtype: ChatCompletionWithHistory
        """
        assert len(function_schema) == len(function_map)
        try:
            response = openai.ChatCompletion.create(
                n=self.params.n,
                model=self.model_name,
                messages=message,
                functions=function_schema,
                temperature=self.params.temperature,
                max_tokens=self.params.max_tokens,
                top_p=self.params.top_p,
                frequency_penalty=self.params.frequency_penalty,
                presence_penalty=self.params.presence_penalty,
            )
            response_message = response.choices[0]["message"]

            if response_message.get("function_call"):
                function_name = response_message["function_call"]["name"]
                fuction_to_call = function_map[function_name]
                function_args = json.loads(response_message["function_call"]["arguments"])
                function_response = fuction_to_call(**function_args)

                # Postprocess function response
                if isinstance(function_response, str):
                    plugin_cost = 0
                    plugin_token = 0
                elif isinstance(function_response, AgentOutput):
                    plugin_cost = function_response.cost
                    plugin_token = function_response.token_usage
                    function_response = function_response.output
                else:
                    raise Exception("Invalid tool response type. Must be on of [AgentOutput, str]")

                message.append(dict(response_message))
                message.append({"role": "function",
                                "name": function_name,
                                "content": function_response})
                second_response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=message,
                )
                message.append(dict(second_response.choices[0].message))
                return ChatCompletionWithHistory(state="success",
                                                 role=second_response.choices[0].message["role"],
                                                 content=second_response.choices[0].message["content"],
                                                 prompt_token=response.get("usage", {}).get("prompt_tokens", 0) +
                                                              second_response.get("usage", {}).get("prompt_tokens", 0),
                                                 completion_token=response.get("usage", {}).get("completion_tokens", 0) +
                                                                  second_response.get("usage", {}).get("completion_tokens", 0),
                                                 message_scratchpad=message,
                                                 plugin_cost=plugin_cost,
                                                 plugin_token=plugin_token,
                                                 )
            else:
                message.append(dict(response_message))
                return ChatCompletionWithHistory(state="success",
                                                 role=response.choices[0].message["role"],
                                                 content=response.choices[0].message["content"],
                                                 prompt_token=response.get("usage", {}).get("prompt_tokens", 0),
                                                 completion_token=response.get("usage", {}).get("completion_tokens", 0),
                                                 message_scratchpad=message)

        except Exception as exception:
            print("Exception:", exception)
            return ChatCompletionWithHistory(state="error", content=str(exception))

    def function_chat_stream_completion(self, message: List[dict],
                                        function_map: Dict[str, Callable],
                                        function_schema: List[Dict]) -> ChatCompletionWithHistory:
        assert len(function_schema) == len(function_map)
        try:
            response = openai.ChatCompletion.create(
                n=self.params.n,
                model=self.model_name,
                messages=message,
                functions=function_schema,
                temperature=self.params.temperature,
                max_tokens=self.params.max_tokens,
                top_p=self.params.top_p,
                frequency_penalty=self.params.frequency_penalty,
                presence_penalty=self.params.presence_penalty,
                stream=True
            )
            tmp = next(response)
            role = tmp.choices[0].delta["role"]
            _type = "function_call" if tmp.choices[0].delta["content"] is None else "content"
            if _type == "function_call":
                name = tmp.choices[0].delta['function_call']['name']
                yield _type, ChatCompletionWithHistory(state="success", role=role,
                                                       content="{" + f'"name":"{name}", "arguments":',
                                                       message_scratchpad=message)
            for resp in response:
                # print(resp)
                content = resp.choices[0].delta.get(_type, "")
                if isinstance(content, dict):
                    content = content['arguments']
                yield _type, ChatCompletionWithHistory(state="success",
                                                       role=role,
                                                       content=content,
                                                       message_scratchpad=message)

            # result = ''.join(messages)
            # if _type == "function_call":
            #     result = json.loads(result)
            #     function_name = result["name"]
            #     fuction_to_call = function_map[function_name]
            #     function_args = result["arguments"]
            #     function_response = fuction_to_call(**function_args)
            #
            #     # Postprocess function response
            #     if isinstance(function_response, AgentOutput):
            #         function_response = function_response.output
            #     message.append({"role": "function",
            #                     "name": function_name,
            #                     "content": function_response})
            #     second_response = self.function_chat_stream_completion(message=message,function_map=function_map,function_schema=function_schema)
            #     message.append(dict(second_response.choices[0].message))


        except Exception as exception:
            raise exception
            print("Exception:", exception)
            return ChatCompletion(state="error", content=str(exception))
