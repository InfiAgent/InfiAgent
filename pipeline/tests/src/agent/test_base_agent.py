import unittest
from abc import ABC
from unittest import mock

from src.agent import BaseAgent
from src.exceptions.exceptions import InputErrorException
from src.llm import BaseLLM
from src.prompt import PromptTemplate
from src.schemas import AgentType, AgentOutput
from src.tools import BaseTool


class SampleBaseAgent(BaseAgent):
    def run(self, *args, **kwargs) -> AgentOutput:
        pass


class SampleBaseTool(BaseTool, ABC):
    def run(self, req):
        pass

    async def async_run(self, req):
        pass


class TestBaseAgent(unittest.TestCase):

    def setUp(self):
        self.mock_llm = mock.create_autospec(BaseLLM)
        self.mock_prompt_template = mock.create_autospec(PromptTemplate)
        self.agent = SampleBaseAgent(name='TestAgent', type=AgentType.react, version='1.0',
                                     description='Test Description', prompt_template=self.mock_prompt_template)
        self.tool = SampleBaseTool("test_tool", "test_tool")
        self.agent.add_plugin('test_tool', self.tool)

    def test_properties(self):
        self.assertEqual(self.agent.name, 'TestAgent')
        self.assertEqual(self.agent.type, AgentType.react)
        self.assertEqual(self.agent.version, '1.0')
        self.assertEqual(self.agent.description, 'Test Description')
        self.assertEqual(self.agent.prompt_template, self.mock_prompt_template)

    # For llm setter
    def test_llm_setter_happy_path(self):
        self.agent.llm = self.mock_llm
        self.assertEqual(self.agent.llm, self.mock_llm)

    def test_llm_setter_input_error(self):
        with self.assertRaises(InputErrorException):
            self.agent.llm = 'invalid_llm'

    # For add_plugin
    def test_add_plugin_happy_path(self):
        self.agent.add_plugin('test_tool', 'test_tool_instance')
        self.assertIn('test_tool', self.agent.plugins_map)

    def test_add_plugin_input_error(self):
        with self.assertRaises(InputErrorException):
            self.agent.add_plugin('', None)

    def test_get_prompt_template_dict(self):
        # Case: Input is a dictionary
        with mock.patch.object(BaseAgent, '_parse_prompt_template', return_value=self.mock_prompt_template):
            result = self.agent._get_prompt_template({'test_key': 'dict'})
            self.assertEqual(result, {'test_key': self.mock_prompt_template})

    def test_get_prompt_template_instance(self):
        # Case: Input is a PromptTemplate instance
        prompt_instance = PromptTemplate(input_variables=["foo"], template="Say {foo}")
        result = self.agent._get_prompt_template(prompt_instance)
        self.assertEqual(result, prompt_instance)

    def test_clear(self):
        # assuming clear method does nothing as per the provided implementation
        self.agent.clear()

    def test_get_plugin_tool_function(self):
        function_map = self.agent.get_plugin_tool_function()
        self.assertIn('test_tool', function_map)
        self.assertEqual(function_map['test_tool'], self.tool.run)

    def test_get_plugin_tool_async_function(self):
        function_map = self.agent.get_plugin_tool_async_function()
        self.assertIn('test_tool', function_map)
        self.assertEqual(function_map['test_tool'], self.tool.async_run)


if __name__ == '__main__':
    unittest.main()
