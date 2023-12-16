"""Prompt schema definition."""
from abc import ABC, abstractmethod
from string import Formatter
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Extra, root_validator

from ..exceptions.exceptions import InputErrorException
from ..schemas import AgentAction, AgentObservation, BaseAgentResponse

OBSERVATION_KEY = "Observation"
THOUGHT_KEY = "Thought"
FINAL_ANSWER_KEY = "FinalAnswer"

DEFAULT_OBSERVATION = "Observation:"
DEFAULT_THOUGHT = "Thought:"
DEFAULT_FINAL_ANSWER = "Final Answer:"


class PromptTemplate(BaseModel, ABC):
    _input_variables: List[str]
    _template: str
    _keywords: Dict[str, str]
    _name: str
    _validate_template: bool
    _skip_on_failure: bool

    class Config:
        extra = Extra.forbid

    @property
    def input_variables(self) -> List[str]:
        return self._input_variables

    @property
    def template(self) -> str:
        return self._template

    @property
    def keywords(self) -> Dict[str, str]:
        return self._keywords

    @property
    def name(self) -> str:
        return self._name

    def format(self, **kwargs):
        if not set(self._input_variables).issubset(kwargs.keys()):
            missing_keys = set(self._input_variables) - kwargs.keys()
            raise InputErrorException(f"Missing keys in prompt template: {', '.join(missing_keys)}")

        filtered_kwargs = {key: kwargs[key] for key in self._input_variables if key in kwargs}

        return self._template.format(**filtered_kwargs)

    def construct_scratchpad(self, intermediate_steps: List[BaseAgentResponse]) -> str:
        """Construct the scratchpad that lets the agent continue its thought process."""
        thoughts = ""

        for agent_response in intermediate_steps:
            if isinstance(agent_response, AgentAction):
                # for agent action, use thought
                thoughts += agent_response.raw_output
            elif isinstance(agent_response, AgentObservation):
                # for agent observation use observation
                thoughts += f"\n{self.keywords.get(OBSERVATION_KEY, DEFAULT_OBSERVATION)}\n" \
                            f"{agent_response.formatted_output}\n\n" \
                            f"{self.keywords.get(THOUGHT_KEY, DEFAULT_THOUGHT)}\n"

        return thoughts

    @classmethod
    @root_validator(skip_on_failure=True)
    def template_is_valid(cls, values: Dict) -> Dict:
        """Check that template and input variables are consistent."""
        if values["validate_template"]:
            try:
                dummy_input = {var: "" for var in values["input_variables"]}
                Formatter().format(values["template"], **dummy_input)
            except KeyError as e:
                raise InputErrorException("Invalid prompt schema; check for mismatched or missing input parameters. ")\
                    from e
        return values
