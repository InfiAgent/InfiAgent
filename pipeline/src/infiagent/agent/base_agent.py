import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Callable, Union, AsyncGenerator

from ..exceptions.exceptions import InputErrorException
from ..prompt import PromptTemplate
from ..schemas import AgentOutput, AgentType, AgentResponse

from ..llm.base_llm import BaseLLM

from ..tools import BaseTool
from ..utils import Config, get_logger

import os
from importlib import import_module

logger = get_logger()


LLM_CONF_OVERRIDE_KEY = ['psm', 'dc', 'temperature', 'top_p', 'top_k', 'max_tokens']


class BaseAgent(ABC):
    """Base Agent class defining the essential attributes and methods for an ALM Agent.
    """

    def __init__(self, **kwargs):
        """
        Initializes an instance of the Agent class.
        """
        # Set default values
        default_config = {
            'name': 'agent',
            'type': AgentType.react,
            'version': '',
            'description': '',
            'prompt_template': None,
            'auth': {}
        }
        # Update default values with provided config
        default_config.update(kwargs)

        # Access configuration data with a known default value
        auth = default_config['auth']
        self._set_auth_env(auth)

        self._name: str = default_config['name']
        self._type: AgentType = default_config['type']
        self._version: str = default_config['version']
        self._description: str = default_config['description']
        self.__prompt_template: Union[PromptTemplate, None] = \
            self._get_prompt_template(default_config['prompt_template'])
        self.__llm: Union[BaseLLM, None] = None
        self.__plugins_map: Dict = {}
        self.__plugin_tool_function = {}
        self.__plugin_tool_async_function = {}
        self.__plugin_tool_description = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> AgentType:
        return self._type

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return self._description

    @property
    def prompt_template(self) -> PromptTemplate:
        return self.__prompt_template

    @property
    def llm(self) -> Union[BaseLLM, None]:
        return self.__llm

    @llm.setter
    def llm(self, llm_client: BaseLLM):
        if llm_client is None or not isinstance(llm_client, BaseLLM):
            raise InputErrorException("Invalid llm client {}".format(type(llm_client)))
        self.__llm = llm_client

    @property
    def plugins_map(self) -> Dict:
        return self.__plugins_map.copy()  # Return a copy to prevent external modification

    def add_plugin(self, tool_name: str, tool):
        if not tool_name or not tool:
            raise InputErrorException("Adding invalid tool name: {}, type {}".format(tool_name, type(tool)))
        self.__plugins_map[tool_name] = tool

    def _set_auth_env(self, obj):
        """This method sets environment variables for authentication.
        """
        for key in obj:
            os.environ[key] = obj.get(key)

    def _get_prompt_template(self, obj):
        """This method returns a prompt template instance based on the provided configuration.
        """
        assert isinstance(obj, dict) or isinstance(obj, PromptTemplate)
        if isinstance(obj, dict):
            return {
                key: self._parse_prompt_template(obj[key]) for key in obj
            }
        elif isinstance(obj, PromptTemplate):
            ans = self._parse_prompt_template(obj)
            return ans
        else:
            raise InputErrorException("Invalid PromptTemplate, it should be a dict or PromptTemplate. But get {}"
                                      .format(type(obj)))

    def _parse_prompt_template(self, obj: Union[dict, PromptTemplate]):
        """This method parses the prompt template configuration and returns a prompt template instance.
        """
        assert isinstance(obj, dict) or isinstance(obj, PromptTemplate)
        if isinstance(obj, PromptTemplate):
            return obj
        return PromptTemplate(input_variables=obj['input_variables'],
                              template=obj['template'],
                              validate_template=bool(obj.get('validate_template', True)))

    @classmethod
    def _get_basic_instance_from_config(cls, config_data):
        agent_module_name = config_data.get("module_name", None)
        agent_class_name = config_data.get("class_name", None)
        if not agent_module_name or not agent_class_name:
            raise InputErrorException("Agent module_name and class_name required, please check your config")

        module = import_module(agent_module_name)
        clazz = getattr(module, agent_class_name)
        agent_instance = clazz(**config_data)
        return agent_instance

    @classmethod
    def from_config_path_and_kwargs(cls, config_path, **kwargs):
        config_data = Config.load(config_path)
        logger.info(f"Use config from path {config_path} to init agent : {config_data}")
        agent_instance = cls._get_basic_instance_from_config(config_data)

        if 'llm' in config_data and 'params' in config_data['llm']:
            for param in LLM_CONF_OVERRIDE_KEY:
                if param in kwargs and kwargs[param]:
                    logger.info(f"Overwrite with new {param} {kwargs[param]}")
                    config_data['llm']['params'][param] = kwargs[param]

        assert isinstance(agent_instance, BaseAgent)
        agent_instance._init_llm(config_data.get("llm", {}))
        agent_instance._init_plugins(config_data.get('plugins', []))
        return agent_instance

    def _init_llm(self, obj):
        """
            This method parses the Language Model Manager (LLM) configuration and returns an LLM instance.

            :param obj: A configuration dictionary or string.
            :type obj: dict or str
            :raises ValueError: If the specified LLM is not supported.
            :return: An LLM instance.
            :rtype: BaseLLM
        """
        if isinstance(obj, str):
            name = obj
            model_params = dict()
        else:
            name = obj.get('model_name', None)
            model_params = obj.get('params', dict())

        module_name = obj['module_name']
        class_name = obj['class_name']

        module = import_module(module_name)
        clazz = getattr(module, class_name)

        llm = clazz(model_name=name, params=model_params)
        self.llm = llm

    def _init_plugins(self, configs):
        """
            This method parses the plugin configuration and add each plugin into the plugins_map.
        """
        assert isinstance(configs, list)
        for plugin_config in configs:
            if plugin_config.get('type', "") == 'agent':
                # Agent as plugin
                agent = BaseAgent.from_config_path_and_kwargs(plugin_config['config'])
                self.plugins_map[plugin_config['name']] = agent
            else:
                # Tools as plugin
                params = plugin_config.get('params', dict())
                tool = BaseTool.from_config(config_input=plugin_config['config'], **params)
                self.plugins_map[tool.name] = tool

    @classmethod
    async def async_from_config_path_and_kwargs(cls, config_path, **kwargs):
        config_data = Config.load(config_path)
        logger.info(f"Use config from path {config_path} to init agent : {config_data}")
        agent_instance = cls._get_basic_instance_from_config(config_data)

        # override default config with user input
        if 'llm' in config_data and 'params' in config_data['llm']:
            for param in LLM_CONF_OVERRIDE_KEY:
                if param in kwargs and kwargs[param]:
                    logger.info(f"Overwrite with new {param} {kwargs[param]}")
                    config_data['llm']['params'][param] = kwargs[param]

        # Create tasks for llm and each individual plugin
        llm_config = config_data.get("llm", {})
        plugin_configs = config_data.get('plugins', [])

        
        # Create tasks for llm and each individual plugin
        llm_task = asyncio.create_task(cls._async_init_llm(llm_config))
        plugin_tasks = [asyncio.create_task(cls._async_init_plugin(plugin_config)) for
                        plugin_config in plugin_configs]
        
        
        # Gather results
        llm, *plugins = await asyncio.gather(llm_task, *plugin_tasks)
        
        agent_instance.llm = llm
        for plugin in plugins:
            plugin_name, plugin_instance = plugin
            agent_instance.add_plugin(plugin_name, plugin_instance)
        return agent_instance

    @classmethod
    async def _async_init_llm(cls, llm_config):
        llm_model_name = llm_config.get("module_name", None)
        llm_class_name = llm_config.get("class_name", None)
        if not llm_model_name or not llm_class_name:
            raise InputErrorException("Agent LLM module_name and class_name required, please check your config")
        module = import_module(llm_model_name)
        clazz = getattr(module, llm_class_name)
        assert issubclass(clazz, BaseLLM), f"{clazz} is not a subclass of BaseLLM"
        llm_instance = await clazz.create(config_data=llm_config)
        return llm_instance

    @classmethod
    async def _async_init_plugin(cls, plugin_config):
        
        if plugin_config.get('type', "") == 'agent':
            # Agent as plugin
            agent = await BaseAgent.async_from_config_path_and_kwargs(plugin_config['config'])
            return plugin_config['name'], agent
        else:
            # Tool as plugin
            params = plugin_config.get('params', dict())
            name = plugin_config.get('name', None)
            config = plugin_config['config']
            
            tool = await BaseTool.async_from_config(config_input=config, **params)
            
            if name is None:
                name = tool.name
            logger.info("Init tool with name [{}], and description [{}]".format(name, tool.description))
            return name, tool

    @abstractmethod
    def run(self, *args, **kwargs) -> [AgentResponse, None]:
        """Abstract method to be overridden by child classes for running the agent.

        :return: The output of the agent.
        :rtype: AgentOutput
        """
        pass

    async def async_run(self, *args, **kwargs) -> AsyncGenerator[AgentResponse, None]:
        """Abstract method to be overridden by child classes for running the agent.

        :return: The output of the agent.
        """
        yield self.run(*args, **kwargs)

    def _get_plugin_function_map(self, method_name: str) -> Dict[str, Callable]:
        if method_name == "run" and self.__plugin_tool_function:
            return self.__plugin_tool_function
        elif method_name == "async_run" and self.__plugin_tool_async_function:
            return self.__plugin_tool_async_function

        function_map = {}

        for name, plugin_tool in self.plugins_map.items():
            if isinstance(plugin_tool, (BaseTool, BaseAgent)):
                function_map[name] = getattr(plugin_tool, method_name)
            else:
                logger.warning(f"No support for plugin name {name} of type {type(plugin_tool)}")

        if method_name == "run":
            self.__plugin_tool_function = function_map
        elif method_name == "async_run":
            self.__plugin_tool_async_function = function_map

        return function_map

    def get_plugin_tool_function(self) -> Dict[str, Callable]:
        """Format the function map for the function API.

        :return: The function map.
        :rtype: Dict[str, Callable]
        """
        return self._get_plugin_function_map("run")

    def get_plugin_tool_async_function(self) -> Dict[str, Callable]:
        """Format the function map for the function API.

        :return: The function map.
        :rtype: Dict[str, Callable]
        """
        return self._get_plugin_function_map("async_run")

    def _get_plugin_description(self):
        if self.__plugin_tool_description:
            return self.__plugin_tool_description

        descriptions = ""
        try:
            for plugin_name, plugin in self.plugins_map.items():
                descriptions += f"{plugin_name}[input]: {plugin.description}\n"
        except Exception as e:
            err_msg = "Failed to get plugin tool name and description. error: {}".format(str(e))
            raise InputErrorException(err_msg) from e

        self.__plugin_tool_description = descriptions
        return descriptions

    def clear(self):
        """
        Clear and reset the agent.
        """
        pass
