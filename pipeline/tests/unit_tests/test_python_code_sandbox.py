from unittest.mock import MagicMock

import pytest

import src.schemas.sandbox_models as dm
from src.tools import AsyncPythonSandBoxTool, PythonSandBoxToolResponse

# from src.tools.code_sandbox


# Mock SandboxClient
@pytest.fixture
def mock_client():
    client = MagicMock()
    return client


# Setup PythonSandBoxTool with the mocked client
@pytest.fixture
def tool(mock_client):
    tool = AsyncPythonSandBoxTool(name="Sandbox", description="Remote code sandbox")
    tool.client = mock_client
    return tool


def test_upload_file(tool, mock_client):
    mock_client.upload_file.return_value = dm.UploadOutput(code=0, message="succeed", data="/mnt/file.txt")
    response = tool.upload_file("/path/to/file.txt")
    assert isinstance(response, PythonSandBoxToolResponse)
    assert response.output_text == "Successfully uploaded file to server's path: /mnt/file.txt"


def test_download_file(tool, mock_client):
    mock_client.download_file.return_value = dm.DownloadSuccessOutput(file_name="file.txt", content="hello world")
    response = tool.download_file("file.txt")
    assert isinstance(response, PythonSandBoxToolResponse)
    assert response.output_text == "Successfully downloaded file: file.txt"
    assert response.raw_output.content == "hello world"

def test_extract_code(tool):
    test_str = '''```python
    import pandas as pd

    # Load the data
    df = pd.read_csv('/mnt/0020400390.csv')

    # Checking the first few records
    df.head()
    ```'''

    test_str2 = '''```
    import pandas as pd

    # Load the data
    df = pd.read_csv('/mnt/0020400390.csv')

    # Checking the first few records
    df.head()
    ```'''

    extracted_code = tool.input_handler(test_str)
    assert extracted_code == '''import pandas as pd

    # Load the data
    df = pd.read_csv('/mnt/0020400390.csv')

    # Checking the first few records
    df.head()'''

    extracted_code2 = tool.input_handler(test_str2)
    assert extracted_code2 == '''import pandas as pd

    # Load the data
    df = pd.read_csv('/mnt/0020400390.csv')

    # Checking the first few records
    df.head()'''


def test_run_code_success(tool, mock_client):
    # code execute successful, stdout
    code = "```python\nabc\n```"
    mock_client.run_code.return_value = dm.RunCodeOutput(
        code=0,
        message="succeed",
        data=dm.CodeRunData(is_partial=False,
                            result=dm.CodeRunResult(
                                code_output_result=[dm.CodeOutput(type="stdout", content="hello\n")],
                                deleted_files=[],
                                new_generated_files=[])))
    response = tool.run(code)
    assert isinstance(response, PythonSandBoxToolResponse)
    assert response.output_text == "Ran code\nSTDOUT:\nhello\n\n"

    # code execute successful, image
    code = "```python\nabc\n```"
    mock_client.run_code.return_value = dm.RunCodeOutput(code=0,
                                                         message="succeed",
                                                         data=dm.CodeRunData(
                                                             is_partial=False,
                                                             result=dm.CodeRunResult(code_output_result=[
                                                                 dm.CodeOutput(type="image",
                                                                               content="https://example.com/image.png")
                                                             ],
                                                                                     deleted_files=[],
                                                                                     new_generated_files=[])))
    response = tool.run(code)
    assert isinstance(response, PythonSandBoxToolResponse)
    assert response.output_text == "Ran code\nGenerated an image: https://example.com/image.png\n"

    # code generated output file
    code = "```python\nabc\n```"
    mock_client.run_code.return_value = dm.RunCodeOutput(
        code=0,
        message="succeed",
        data=dm.CodeRunData(is_partial=False,
                            result=dm.CodeRunResult(code_output_result=[],
                                                    deleted_files=[],
                                                    new_generated_files=["/mnt/qr.jpg", "/mnt/qr2.jpg"])))
    mock_client.download_file.return_value = dm.DownloadSuccessOutput(file_name="qr.jpg", content="hello world")
    response = tool.run(code)
    assert isinstance(response, PythonSandBoxToolResponse)
    file_str = ",".join(response.raw_output.data.result.new_generated_files)
    assert response.output_text == f"Ran code\nGenerated files on server: {file_str}\n"

    # code deleted files
    code = "```python\nabc\n```"
    mock_client.run_code.return_value = dm.RunCodeOutput(
        code=0,
        message="succeed",
        data=dm.CodeRunData(is_partial=False,
                            result=dm.CodeRunResult(code_output_result=[],
                                                    deleted_files=["/mnt/qr.jpg", "/mnt/qr2.jpg"],
                                                    new_generated_files=[])))
    response = tool.run(code)
    assert isinstance(response, PythonSandBoxToolResponse)
    assert response.output_text == "Ran code\nDeleted files from server: /mnt/qr.jpg,/mnt/qr2.jpg\n"

    # everything
    code = "```python\nabc\n```"
    mock_client.run_code.return_value = dm.RunCodeOutput(
        code=0,
        message="succeed",
        data=dm.CodeRunData(is_partial=False,
                            result=dm.CodeRunResult(code_output_result=[
                                dm.CodeOutput(type="image", content="https://example.com/image.png"),
                                dm.CodeOutput(type="stdout", content="Plotted and saved files"),
                                dm.CodeOutput(type="stderr", content="Something is deprecated")
                            ],
                                                    deleted_files=["/mnt/qr.jpg", "/mnt/qr2.jpg"],
                                                    new_generated_files=["/mnt/plot.png", "/mnt/plot2.png"])))
    response = tool.run(code)
    assert isinstance(response, PythonSandBoxToolResponse)
    generated_file_str = ",".join(response.raw_output.data.result.new_generated_files)
    expected_str = "Ran code\n" + \
                   "Deleted files from server: /mnt/qr.jpg,/mnt/qr2.jpg\n" + \
                   f"Generated files on server: {generated_file_str}\n" + \
                   "Generated an image: https://example.com/image.png\n" + \
                   "STDOUT:\n" + \
                   "Plotted and saved files\n" + \
                   "STDERR:\n" + \
                   "Something is deprecated\n"
    assert response.output_text == expected_str


def test_run_code_timeout(tool, mock_client):
    server_return = {
        "code": 0,
        "data": {
            "is_partial": True,
            "result": {
                "code_output_result": [],
                "deleted_files": [],
                "new_generated_files": []
            }
        },
        "message": "the code doesn't finish in timeout value 3"
    }
    mock_client.run_code.return_value = dm.RunCodeOutput(**server_return)
    response = tool.run("```python\nabc\n```")
    assert isinstance(response, PythonSandBoxToolResponse)
    expected_str = "Ran code but was not fully successful\n" + \
                   "What happened: the code doesn\'t finish in timeout value 3\n"
    assert response.output_text == expected_str
