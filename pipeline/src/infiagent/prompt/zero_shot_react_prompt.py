from ..prompt import PromptTemplate, OBSERVATION_KEY, THOUGHT_KEY, FINAL_ANSWER_KEY, DEFAULT_OBSERVATION, \
    DEFAULT_THOUGHT, DEFAULT_FINAL_ANSWER


class ZeroShotReactPrompt(PromptTemplate):
    _input_variables = ["instruction", "agent_scratchpad", "tool_names", "tool_description"]
    _template = (
        "Answer the following questions as best you can."
        "You have access to the following tools:\n"
        "{tool_description}.\n"
        "Use the following format:\n\n"
        "Question: the input question you must answer\n"
        "Thought: you should always think about what to do\n\n"
        "Action: the action to take, should be one of [{tool_names}]\n\n"
        "Action Input:\n```python\n[the input to the action]\n```\n"
        "Observation: the result of the action\n\n"
        "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
        "Thought: I now know the final answer\n"
        "Final Answer: the final answer to the original input question\n"
        "If you have any files outputted write them to \"./\"\n"
        "Do not use things like plot.show() as it will not work instead write them out \"./\"\n"
        "Begin!\n\n"
        "Question: {instruction}\nThought:\n"
        "{agent_scratchpad}\n"
    )
    _keywords = {
        OBSERVATION_KEY: DEFAULT_OBSERVATION,
        THOUGHT_KEY: DEFAULT_THOUGHT,
        FINAL_ANSWER_KEY: DEFAULT_FINAL_ANSWER
    }
    _name = 'ZeroShotReactPrompt'
    _validate_template = True
    _skip_on_failure = True

    def __init__(self, **data):
        super().__init__(**data)
