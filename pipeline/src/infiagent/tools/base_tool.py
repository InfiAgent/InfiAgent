from dataclasses import dataclass
from typing import Optional, Type
from abc import ABC
from importlib import import_module

from ..exceptions.exceptions import InvalidConfigException
from ..utils import Config


@dataclass
class BaseToolRequest(ABC):
    input_text: Optional[str]


@dataclass
class BaseToolResponse(ABC):
    output_text: Optional[str]


# BaseTool
class BaseTool(ABC):
    _name = None
    _description = None

    def __init__(self, name, description, **kwargs):
        self._name = name
        self._description = description
        self.setup()

    @property
    def name(self):
        """Getter for name."""
        return self._name

    @property
    def description(self):
        """Getter for description."""
        return self._description

    @classmethod
    def from_config(cls, config_input, **kwargs):
        """Create a BaseTool instance from a config file path or a config data dictionary.

        :param config_input: Either a file path to a config file or a config data dictionary.
        :type config_input: str or dict
        :param kwargs: Additional keyword arguments to pass to the class constructor.
        :return: A BaseTool instance.
        :rtype: BaseTool
        """
        if isinstance(config_input, str):
            # If config_input is a string, assume it's a file path.
            config_data = Config.load(config_input)
        elif isinstance(config_input, dict):
            # If config_input is a dict, use it directly as config_data.
            config_data = config_input
        else:
            raise InvalidConfigException(
                f"Invalid config_input type: {type(config_input)}. "
                "Expected str (file path) or dict (config data)."
            )

        module_name = config_data['module_name']
        class_name = config_data['class_name']
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        return clazz(**config_data, **kwargs)

    @classmethod
    async def async_from_config(cls, config_input, **params):
        """Asynchronously create a BaseTool instance from a config file path or a config data dictionary.

        :param config_input: Either a file path to a config file or a config data dictionary.
        :type config_input: str or dict
        :param params: Additional parameters to pass to the create method.
        :return: A BaseTool instance.
        :rtype: BaseTool
        """
        

        if isinstance(config_input, str):
            # If config_input is a string, assume it's a file path.
            config_data = Config.load(config_input)
        elif isinstance(config_input, dict):
            # If config_input is a dict, use it directly as config_data.
            config_data = config_input
        else:
            raise InvalidConfigException(
                f"Invalid config_input type: {type(config_input)}. "
                "Expected str (file path) or dict (config data)."
            )

        
        module_name = config_data['module_name']
        class_name = config_data['class_name']
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        
        return await clazz.create(config_data, **params)

    @classmethod
    async def async_from_config_path(cls, config_path, **params):
        return await cls.async_from_config_data(config_data=Config.load(config_path), **params)

    @classmethod
    async def async_from_config_data(cls, config_data, **params):
        module_name = config_data['module_name']
        class_name = config_data['class_name']

        module = import_module(module_name)
        clazz = getattr(module, class_name)

        return await clazz.create(config_data, **params)

    @classmethod
    async def create(cls, config_data, **params):
        """
        Async create tool instance. init cannot be async, so wrap async init logic here.
        """
        pass

    def setup(self):
        pass

    def run(self, req: BaseToolRequest):
        pass

    async def async_run(self, req: BaseToolRequest):
        """
        Async run tool.
        """
        return self.run(req)
