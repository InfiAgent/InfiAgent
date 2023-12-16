from .logger import get_logger

logger = get_logger()

MODEL_NAME_TO_CONFIG = {
    "OPEN_AI": "../configs/agent_configs/react_agent_gpt4_async.yaml",
    "AZURE_OPEN_AI": "../configs/agent_configs/react_agent_azureopenai_gpt_4_async.yaml",
    "AZURE_GPT35_TURBO": "../configs/agent_configs/react_agent_azureopenai_gpt_35_turbo_async.yaml",
    "AZURE_GPT4": "../configs/agent_configs/react_agent_azureopenai_gpt_4_async.yaml",
    "LLAMA": "../configs/agent_configs/react_agent_llama_async.yaml",
    "OPT": "../configs/agent_configs/react_agent_opt_async.yaml",

}


def get_model_config_path(input_model_name):
    if input_model_name is None:
        model_name = "openai"
    else:
        model_name = input_model_name
    
    # check if same model name
    if model_name in MODEL_NAME_TO_CONFIG:
        return MODEL_NAME_TO_CONFIG[model_name]
    
    # check if converted to capital letters
    if model_name.upper() in MODEL_NAME_TO_CONFIG:
        return MODEL_NAME_TO_CONFIG[model_name.upper()]

    if "openai" in model_name:
        return MODEL_NAME_TO_CONFIG["AZURE_OPEN_AI"]

    elif "llama" in model_name:
        return MODEL_NAME_TO_CONFIG["LLAMA"]
    elif "opt" in model_name:   
        return MODEL_NAME_TO_CONFIG["OPT"]
    else:
        logger.warning("unknown model name, use official.")
        return MODEL_NAME_TO_CONFIG["AZURE_OPEN_AI"]
