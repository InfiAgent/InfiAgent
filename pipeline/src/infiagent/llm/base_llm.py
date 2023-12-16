from abc import ABC

from ..exceptions.exceptions import InputErrorException
from ..schemas import BaseCompletion


class BaseLLM(ABC):

    def __init__(self, model_name: str, params: dict, **kwargs):
        self.__model_name = model_name
        self.__params = params

    @classmethod
    async def create(cls, config_data: dict):
        pass

    @property
    def model_name(self) -> str:
        return self.__model_name

    @model_name.setter
    def model_name(self, model_name):
        if model_name is None:
            raise InputErrorException("Invalid model_name {}".format(model_name))
        self.__model_name = model_name

    @property
    def params(self) -> dict:
        return self.__params

    def completion(self, prompt) -> BaseCompletion:
        pass

    async def async_completion(self, prompt) -> BaseCompletion:
        pass

