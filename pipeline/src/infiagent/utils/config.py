import yaml
from typing import Dict, AnyStr, Union, Any
from pathlib import Path

from ..prompt import SimpleReactPrompt, ZeroShotReactPrompt
from .logger import get_logger

logger = get_logger()


class Config:
    """
    A class for loading and creating configuration dictionaries from files or dictionaries.
    """

    @staticmethod
    def _prompt_constructor(loader, node):
        value = node.value
        if value == "SimpleReactPrompt":
            return SimpleReactPrompt()
        elif value == "ZeroShotReactPrompt":
            return ZeroShotReactPrompt()
        else:
            logger.warning(f"Unknown prompt name: {value}. use default SimpleReactPrompt")
            return SimpleReactPrompt()

    @staticmethod
    def load(path: Union[Path, AnyStr]) -> Dict[AnyStr, Any]:
        """
           Load a configuration dictionary from a YAML file.

           :param path: The path to the configuration file.
           :type path: Union[Path, AnyStr]
           :raises FileNotFoundError: If the file is not found.
           :raises yaml.YAMLError: If a YAML error occurred while loading the file.
           :raises Exception: If an unexpected error occurred.
           :return: A dictionary containing the configuration.
           :rtype: Dict[AnyStr, Any]
       """
        # logger the start of the loading process
        logger.info(f"Starting to load configuration from {path}")

        # Register the custom prompt constructor with PyYAML
        yaml.add_constructor('!prompt', Config._prompt_constructor)

        try:
            with open(path, "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
                logger.info(f"Successfully loaded configuration from {path}")
                return config
        except FileNotFoundError:
            logger.error(f"Config file {path} not found")
            raise FileNotFoundError(f"Config file {path} not found")
        except yaml.YAMLError as e:
            logger.error(f"YAML error occurred while loading the configuration: {str(e)}", exc_info=True)
            raise yaml.YAMLError(e)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
            raise Exception(e)

    @staticmethod
    def from_dict(config: Dict[AnyStr, Any]) -> Dict[AnyStr, Any]:
        """
        Create a configuration dictionary from a Python dictionary.

        :param config: A dictionary containing configuration parameters.
        :type config: Dict[AnyStr, Any]
        :return: A dictionary containing the configuration.
        :rtype: Dict[AnyStr, Any]
        """
        logger.info(f"Creating Config from dictionary")
        return config
