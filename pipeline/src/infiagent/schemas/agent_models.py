from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import List, NamedTuple, Optional, Union

from pydantic import BaseModel

from ..schemas.sandbox_models import *


@dataclass
class BaseAgentResponse:
    """Base Agent step result, contains formatted output string."""
    formatted_output: str
    raw_output: str


@dataclass
class AgentAction(BaseAgentResponse):
    """
    Agent's action to take.
    """
    tool: str
    tool_input: Union[str, dict]


@dataclass
class AgentObservation(BaseAgentResponse):
    """
    Agent's action to take.
    """
    tool: str


@dataclass
class AgentFinish(BaseAgentResponse):
    """Agent's return value when finishing execution."""
    pass


class AgentType(Enum):
    """
    Enumerated type for agent types.
    """
    openai = "openai"
    react = "react"
    rewoo = "rewoo"
    vanilla = "vanilla"
    openai_memory = "openai_memory"

    @staticmethod
    def get_agent_class(_type: AgentType):
        """
        Get agent class from agent type.
        :param _type: agent type
        :return: agent class
        """
        if _type == AgentType.react:
            from ..agent.react import ReactAgent
            return ReactAgent
        else:
            raise ValueError(f"Unknown agent type: {_type}")


class AgentOutput(BaseModel):
    """
    Pydantic model for agent output.
    """
    output: str
    cost: float
    token_usage: int


@dataclass
class AgentRequest:
    sandbox_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    input_files: List[MediaFile] = field(default_factory=list)
    sandbox_status: Optional[SandboxStatus] = None
    is_cn: bool = False



@dataclass
class AgentResponse:
    output_text: str
    raw_output_text: str
    output_files: List[MediaFile] = field(default_factory=list)
    sandbox_id: Optional[str] = None
    sandbox_status: Optional[SandboxStatus] = None
    turn_level_prompt: Optional[List[str]] = None
    turn_level_response: Optional[List[str]] = None


class RoleType(Enum):
    User = 0
    System = 1
    Agent = 2

    @classmethod
    def _missing_(cls, name):
        # If the input is a string, perform case-insensitive matching
        if isinstance(name, str):
            for member in cls:
                if member.name.lower() == name.lower():
                    return member
        return super()._missing_(name)


@dataclass
class Message(abc.ABC):
    role: RoleType
    content: str
    raw_content: str = ""

    @staticmethod
    def parse_from_dict(data):
        data['role'] = RoleType(data['role'])
        # Add a check for raw_content in legacy data
        if 'raw_content' not in data:
            data['raw_content'] = ""
        return Message(**data)

    def to_dict(self):
        role_value = self.role.value if isinstance(self.role, RoleType) else self.role
        return {
            "role": role_value,
            "content": self.content,  # Fixed the missing comma here
            "raw_content": self.raw_content
        }


@dataclass
class MediaFile:
    file_name: Optional[str] = None 
    file_content: Optional[bytes] = None  
    tos_path: Optional[str] = None  
    sandbox_path: Optional[str] = None 

    def __dict__(self):
        return {
            'file_name': self.file_name if self.file_name is not None else "",
            'file_content': self.file_content if self.file_content is not None else "",
            'tos_path': self.tos_path if self.tos_path is not None else "",
            'sandbox_path': self.sandbox_path if self.sandbox_path is not None else "",
        }
