from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, NamedTuple, Union

from pydantic import BaseModel

try:
    import torch
except ImportError:
    pass



class BaseCompletion(BaseModel):
    state: str  # "success" or "error"
    content: str
    prompt_token: int = 0
    completion_token: int = 0

    def to_dict(self):
        return dict(
            state=self.state,
            content=self.content,
            prompt_token=self.prompt_token,
            completion_token=self.completion_token,
        )


class ChatCompletion(BaseCompletion):
    role: str = "assistant"  # "system" or "user" or "assistant"


class ChatCompletionWithHistory(ChatCompletion):
    """Used for function call API"""
    message_scratchpad: List[Dict] = []
    plugin_cost: float = 0.0
    plugin_token: float = 0.0


class BaseParamModel(BaseModel):
    def __eq__(self, other):
        return self.dict() == other.dict()


class OpenAIParamModel(BaseModel):
    """
    OpenAI API parameters
    """
    max_tokens: int = 2048
    temperature: float = 0.2
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    n: int = 1
    stop: list = []

class AzureOpenAIParamModel(BaseModel):
    """
    AzureOpenAI API parameters
    """
    max_tokens: int = 2048
    temperature: float = 0.2
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    n: int = 1
    stop: list = []

class LlamaParamModel(BaseModel):
    """
    AzureOpenAI API parameters
    """
    max_tokens: int = 4096
    temperature: float = 0.2
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    n: int = 1
    stop: list = []

class OptParamModel(BaseModel):
    """
    AzureOpenAI API parameters
    """
    max_tokens: int = 2048
    temperature: float = 0.2
    top_p: float = 1.0
    n: int = 1
    stop: list = []
