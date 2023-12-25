import re
import time
from typing import Union, List, Dict

from werkzeug.datastructures import FileStorage

from .. import BaseAgent
from ...exceptions.exceptions import InternalErrorException, LLMException, SandboxException
from ...schemas import (
    AgentType, AgentRequest, AgentFinish, AgentAction, AgentResponse,
    BaseAgentResponse, AgentObservation, RunCodeOutput, MediaFile
)
from ...tools import PythonSandBoxToolResponse, AsyncPythonSandBoxTool
from ...utils import get_logger, replace_latex_format, extract_and_replace_url, \
    OBSERVATION_PREFIX_CN, OBSERVATION_PREFIX_EN, AGENT_FAILED_CN, AGENT_FAILED_EN, \
    TOOL_INPUT_PREFIX_CN, TOOL_INPUT_PREFIX_EN

SAND_BOX_PLUGIN_NAME = 'python_code_sandbox'
FINAL_ANSWER_INDICATORS = ["Final Answer:", "[END]", "The final Answer", "final answer"]
CODE_BLOCK_START_TAG = '```python'
CODE_BLOCK_TAG = '```'

logger = get_logger()

SAND_BOX_PLUGIN_NAME = 'python_code_sandbox'
FINAL_ANSWER_INDICATORS = ["Final Answer:", "[END]", "The final Answer", "final answer"]
CODE_BLOCK_START_TAG = '```python'
CODE_BLOCK_TAG = '```'
STOP_WORD = ['Observation:']

logger = get_logger()


class AsyncReactAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = self._name or "AsyncReactAgent"
        self._type = AgentType.react
        self.__intermediate_steps: List[BaseAgentResponse] = []

    @property
    def intermediate_steps(self):
        return self.__intermediate_steps

    def run(self, *args, **kwargs):
        pass

    async def sync_to_sandbox(self, file: Union[str, Dict, FileStorage]):
        sandbox_plugin = self.plugins_map.get(SAND_BOX_PLUGIN_NAME)
        if not isinstance(sandbox_plugin, (AsyncPythonSandBoxTool, AsyncPythonSandBoxTool)):
            raise InternalErrorException("SandBox client is not ready for agent, please check init logic.")
        return await sandbox_plugin.sync_to_sandbox(file)

    async def async_run(self, agent_req: AgentRequest):
        instruction = '\n'.join(message.content for message in agent_req.messages)
        async for response in self._chat(instruction, is_cn=agent_req.is_cn):
            yield response

    async def _chat(self, instruction: str, is_cn=False, max_iterations=10,
                    max_single_step_iterations=3):
        current_iteration = 0

        for _ in range(max_iterations):
            current_iteration += 1
            llm_response = await self._single_round_thought(instruction,
                                                            max_llm_iteration=max_single_step_iterations,
                                                            is_cn=is_cn)
            logger.info("Round {} of {}, [LLM raw output]:\n{}\n\n[Formatted output]:\n{}\n"
                        .format(current_iteration, max_iterations, llm_response.raw_output,
                                llm_response.formatted_output))
            yield self.create_agent_response(llm_response.formatted_output, [], llm_response.raw_output)

            if isinstance(llm_response, AgentFinish):
                logger.info("Find final answer, stop iteration.")
                break

            self.intermediate_steps.append(llm_response)
            action_response, cur_output_files = await self._process_agent_action(llm_response, current_iteration,
                                                                                 max_iterations, is_cn)
            logger.info("Round {} of {}, [Plugin raw output]:\n{}\n[Formatted output]:\n{}\n"
                        .format(current_iteration, max_iterations, action_response.raw_output,
                                action_response.formatted_output))
            self.intermediate_steps.append(action_response)

            yield self.create_agent_response(action_response.formatted_output,
                                             cur_output_files,
                                             action_response.raw_output)

        logger.info(f"Finished iteration in {current_iteration}.")

    # TODO update logic to not be sandbox specific, sandbox related logic should be handled in sandbox client
    async def _process_agent_action(self, response, current_iteration, max_iterations, is_cn: bool = False):
        try:
            response.tool = 'python_code_sandbox'
            action_response = await self.get_plugin_tool_async_function()[response.tool](response.tool_input)
            logger.info(
                f"Step {current_iteration} of {max_iterations}. Got agent observation raw output:\n"
                f"{action_response.output_text}")

            if "STDERR" in action_response.output_text:
                formatted_output = self._process_sandbox_output(action_response.output_text)
            else:
                formatted_output = action_response.output_text

            formatted_output = replace_latex_format(formatted_output)
            observation_prefix = OBSERVATION_PREFIX_CN if is_cn else OBSERVATION_PREFIX_EN
            formatted_output = f"{observation_prefix}\n{formatted_output}\n"

            action_observation = AgentObservation(tool=response.tool,
                                                  formatted_output=formatted_output,
                                                  raw_output=action_response.output_text)
            cur_output_files = self._get_output_files(action_response)
            return action_observation, cur_output_files

        except Exception as e:
            logger.error(f"Error occurred while executing tool {response.tool} with input {response.tool_input}. "
                         f"Error: {str(e)}", exc_info=True)
            # TODO: We hard code here as we only have one tool
            raise SandboxException("Error occurred while running the tool") from e

    def _compose_prompt(self, instruction) -> str:
        """
        Compose the prompt from template, worker description, examples and instruction.
        """
        agent_scratchpad = self.prompt_template.construct_scratchpad(self.__intermediate_steps)
        tool_description = self._get_plugin_description()
        tool_names = ", ".join(list(self.plugins_map.keys()))
        if self.prompt_template is None:
            raise InternalErrorException("Agent prompt is none, please check init process")

        return self.prompt_template.format(
            instruction=instruction,
            agent_scratchpad=agent_scratchpad,
            tool_description=tool_description,
            tool_names=tool_names
        )

    async def _single_round_thought(self, instruction: str, max_llm_iteration=3, is_cn: bool = False) -> \
            Union[AgentAction, AgentFinish]:

        llm_iteration_count = 0

        llm_response = None
        while llm_iteration_count <= max_llm_iteration:
            llm_iteration_count += 1
            try:
                llm_response = await self._get_llm_response(instruction)
                action_response = self._parse_output(llm_response.content, is_cn)

                return action_response
            except Exception as e:
                logger.error("LLM iteration {} out of {} failed. Error: {}".
                             format(llm_iteration_count, max_llm_iteration, str(e)), exc_info=True)

                if llm_iteration_count > max_llm_iteration:
                    logger.error("LLM iteration {} exceed max retry {}. Aborting".
                                 format(llm_iteration_count, max_llm_iteration))
                    return AgentFinish(formatted_output=AGENT_FAILED_CN if is_cn else AGENT_FAILED_EN,
                                       raw_output=str(llm_response))

    async def _get_llm_response(self, instruction: str):
        prompt = self._compose_prompt(instruction)
        logger.info("Send prompt to LLM:\n{}".format(prompt))
        response = await self.llm.async_completion(prompt)
        if response.state == "error":
            raise LLMException("Failed to retrieve response from LLM, error: {}".format(str(response.content)))

        logger.info("Got response from llm, raw response content: \n{}".format(response.content))
        return response

    def _parse_output(self, llm_output: str, is_cn: bool = False) -> Union[AgentAction, AgentFinish]:

        for stop_word in STOP_WORD:
            if stop_word in llm_output:
                llm_output = llm_output.split(stop_word)[0].rstrip()
                break

        # Check for Final Answer, if it is final, then just return
        for indicator in FINAL_ANSWER_INDICATORS:
            if indicator in llm_output:
                # got final answer and remove the indicator
                parts = llm_output.split(indicator)
                # formatted_output = ''.join(parts[:-1]).strip()
                formatted_output = ''.join(parts).strip()
                formatted_output = replace_latex_format(formatted_output)
                return AgentFinish(raw_output=llm_output, formatted_output=formatted_output)

        # Updated regex pattern for capturing the expected input format
        ACTION_REGEX_1 = r"(.*?)\n?Action:\s*(.*?)\n?Action\s*Input:\s*```python\n(.*?)```(.*?)$|(.*?)\n?'''(\w+)\n?(.*?)\n?'''(.*?)$"
        ACTION_REGEX_2 = r"(.*?)\n?Action:\s*(.*?)\n?Action\s*Input:\s*```py\n(.*?)```(.*?)$|(.*?)\n?'''(\w+)\n?(.*?)\n?'''(.*?)$"

        action_match = re.search(ACTION_REGEX_1, llm_output, re.DOTALL) or re.search(ACTION_REGEX_2, llm_output, re.DOTALL)

        # Find action, context, and action input, build action response
        if action_match:
            context = action_match.group(1).strip()
            action_tool_description = action_match.group(2).strip()
            action_input = action_match.group(3).strip()

            # Format code
            # TODO: currently we only have one plugin which is sandbox, update to support multiple tools
            format_code_block = self._format_code_block(action_input)

            prefix = TOOL_INPUT_PREFIX_CN if is_cn else TOOL_INPUT_PREFIX_EN
            formatted_output = "{}\n{}\n{}\n".format(context, prefix, format_code_block)
            formatted_output = replace_latex_format(formatted_output)

            return AgentAction(tool=action_tool_description,
                               tool_input=format_code_block,
                               formatted_output=formatted_output,
                               raw_output=llm_output)

        # Not final answer and not action, raise exception
        if not re.search(r"Action\s*:", llm_output, re.DOTALL):
            raise LLMException(f"Missing 'Action' in LLM output: `{llm_output}`")
        elif not re.search(r"Action\s*Input\s*:", llm_output, re.DOTALL):
            raise LLMException(f"Missing 'Action Input' in LLM output: `{llm_output}`")
        else:
            raise LLMException(f"Unrecognized LLM output format: `{llm_output}`")

    def _format_code_block(self, tool_input):
        stripped_tool_input = tool_input.strip()

        if stripped_tool_input.startswith(CODE_BLOCK_START_TAG) and stripped_tool_input.endswith(CODE_BLOCK_TAG):
            if not stripped_tool_input.startswith(CODE_BLOCK_START_TAG + '\n'):
                stripped_tool_input = CODE_BLOCK_START_TAG + '\n' + stripped_tool_input[len(CODE_BLOCK_START_TAG):] + \
                                      '\n'
            formatted_code = stripped_tool_input
        elif stripped_tool_input.startswith(CODE_BLOCK_TAG) and not stripped_tool_input.startswith(
                CODE_BLOCK_START_TAG) and stripped_tool_input.endswith(CODE_BLOCK_TAG):
            formatted_code = CODE_BLOCK_START_TAG + '\n' + stripped_tool_input[len(CODE_BLOCK_TAG):] + '\n'
        else:
            formatted_code = CODE_BLOCK_START_TAG + '\n' + stripped_tool_input + '\n' + CODE_BLOCK_TAG + '\n'

        return formatted_code.encode("utf-8").decode("utf-8")

    def _process_sandbox_output(self, output: str):
        """Function to process the result containing STDERR."""
        if len(output) <= 1000:
            return output

        logger.info("Output contains error, original message is over 1000, trim it for response. ori output: \n{}".
                    format(output))
        rows = output.split("\n")
        # Get the first 500 characters, respecting line boundaries
        top_segment = []
        length = 0
        for sub_p in rows:
            if length + len(sub_p) > 500:
                break
            top_segment.append(sub_p)
            length += len(sub_p)

        # Get the last 500 characters, respecting line boundaries
        bottom_segment = []
        length = 0
        for sub_p in reversed(rows):
            if length + len(sub_p) > 500:
                break
            bottom_segment.insert(0, sub_p)
            length += len(sub_p)

        # Combine the segments with "......" in between
        timed_output = "\n".join(top_segment + ["......"] + bottom_segment)

        return timed_output

    def _get_output_files(self, tool_response) -> list[MediaFile]:
        output_files = []

        if isinstance(tool_response, PythonSandBoxToolResponse) and isinstance(tool_response.raw_output, RunCodeOutput):
            raw_output = tool_response.raw_output

            if raw_output.code == 0 and not raw_output.data.is_partial:
                result_data = raw_output.data.result

                # TODO confirm if we still need output and format
                if len(result_data.new_generated_files) > 0:
                    output_files.extend([MediaFile(tos_path=file.download_link) for file in
                                         result_data.new_generated_files])

                if len(result_data.code_output_result) > 0:
                    output_files.extend(
                        [MediaFile(tos_path=image.content) for image in result_data.code_output_result
                         if image.type == 'image'])

        return output_files

    def _replace_csv_path(self, input_string):
        # Search for the pattern and replace it
        pattern = r'pd\.read_csv\(["\'](.*\.csv)["\']\)'
        replacement = "pd.read_csv('/path/to/your/dataset')"
        updated_string = re.sub(pattern, replacement, input_string)
        return updated_string

    @staticmethod
    def create_agent_response(formatted_output, output_files, raw_output):
        return AgentResponse(output_text=formatted_output, output_files=output_files, raw_output_text=raw_output)

