from ..prompt import FINAL_ANSWER_KEY, OBSERVATION_KEY, THOUGHT_KEY, PromptTemplate


class SimpleReactPrompt(PromptTemplate):
    _input_variables = ["instruction", "agent_scratchpad"]
    _template = "{instruction} \n{agent_scratchpad}"
    _keywords = {
        OBSERVATION_KEY: "[EOS]Observation:",
        THOUGHT_KEY: "[SEP]",
        FINAL_ANSWER_KEY: "[END]"
    }
    _name = 'SimpleReactPrompt'
    _validate_template = True
    _skip_on_failure = True

    def __init__(self, **data):
        super().__init__(**data)
