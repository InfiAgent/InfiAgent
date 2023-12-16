SYSTEM_MESSAGE_PREFIX_EN = '[SYSTEM NOTIFICATION]'
SYSTEM_MESSAGE_PREFIX_CH = '【系统提示】'

FILE_CONVERTED_EN = (
    f"\n{SYSTEM_MESSAGE_PREFIX_EN}\n"
    "If you are seeing this message, it indicates that the CSV file you provided did not use a comma as its "
    "delimiter. We have automatically detected the delimiter of your file and converted it to a comma-separated "
    "format for processing. This means that the processed output may differ from your original input in terms of "
    "delimiters. To ensure delimiter consistency, please convert your file to a comma-separated format before "
    "uploading."
)

FILE_CONVERTED_CH = (
        f"\n{SYSTEM_MESSAGE_PREFIX_CH}\n"
        "如果您看到此消息，表示您提供的CSV文件的分隔符并非逗号(',')。我们已自动检测到您文件的分隔符，并将其转换为逗号分隔的格式进行处理。"
        "这意味着处理后的输出分隔符可能与您原始的输入不同。为确保文件的一致性，请在上传之前将您的CSV文件转换为逗号分隔的格式。"
)

TOOL_INPUT_PREFIX_EN = f"{SYSTEM_MESSAGE_PREFIX_EN} We need to execute with python sandbox with the following code:"
OBSERVATION_PREFIX_EN = f"{SYSTEM_MESSAGE_PREFIX_EN} Running the above tool with the following response: "
TOOL_INPUT_PREFIX_CN = f"{SYSTEM_MESSAGE_PREFIX_CH} 执行如下代码: "
OBSERVATION_PREFIX_CN = f"{SYSTEM_MESSAGE_PREFIX_CH} 代码执行结果为: "
AGENT_FAILED_EN = f"{SYSTEM_MESSAGE_PREFIX_EN} Sorry Agent unable to answer this question due to LLM fail.\n"
AGENT_FAILED_CN = f"{SYSTEM_MESSAGE_PREFIX_CH} 对不起，模型暂时无法回答这个问题.\n"
AGENT_EXCEED_MAX_RETRY_EN = f"{SYSTEM_MESSAGE_PREFIX_EN} Sorry agent unable to answer the questions within max " \
                            f"retry, please try another question."
AGENT_EXCEED_MAX_RETRY_CN = f"{SYSTEM_MESSAGE_PREFIX_CH} 对不起， 模型暂时无法在规定时间内回答这个问题，请换一个问题重试."
