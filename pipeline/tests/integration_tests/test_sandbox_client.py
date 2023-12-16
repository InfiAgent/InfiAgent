"""Integration test for code sandbox client"""

import pytest

import src.schemas.sandbox_models as dm
from src.tools.code_sandbox.async_sandbox_client import AsyncSandboxClient

# Assuming you have some actual session IDs and files to test with.
# For the purpose of this example, I'm using dummy values.
SAMPLE_SESSION_ID = "test_session_id"
SAMPLE_FILE_PATH = "tests/integration_tests/sample_file.txt"
SAMPLE_FILE_NAME = "sample_file.txt"
SAMPLE_IMAGE_PATH = "tests/integration_tests/sample_image.jpg"
SAMPLE_IMAGE_NAME = "sample_image.jpg"


def test_run_code_success():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)

    result = client.run_code("print('Hello World!')", timeout=10)
    assert isinstance(result, dm.RunCodeOutput)
    assert result.data is not None
    assert result.data.is_partial == False
    assert result.data.result is not None
    code_output = result.data.result.code_output_result
    assert len(code_output) == 1
    assert code_output[0].__type == "stdout"
    assert code_output[0].content == "Hello World!\n"


def test_run_code_timeout():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)

    result = client.run_code("while True:\n    pass", timeout=1)
    assert isinstance(result, dm.RunCodeOutput)
    assert result.data.is_partial == True
    assert result.data.result is not None
    assert result.message == "the code doesn't finish in timeout value 1"


def test_run_code_error():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)

    result = client.run_code("print('hello', error='abc')", timeout=10)
    assert isinstance(result, dm.RunCodeOutput)
    assert result.data is not None
    assert result.data.is_partial == False
    assert result.data.result is not None
    code_output = result.data.result.code_output_result
    assert len(code_output) == 1
    assert code_output[0].__type == "stderr"


def test_upload_download_text_file():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)
    result = client.upload_file(SAMPLE_FILE_PATH, SAMPLE_FILE_NAME)
    assert isinstance(result, dm.UploadOutput)
    assert result.message == "succeed"
    assert result.data == f"/mnt/{SAMPLE_FILE_NAME}"

    result = client.download_file(SAMPLE_FILE_NAME)
    assert isinstance(result, dm.DownloadSuccessOutput)
    with open(SAMPLE_FILE_PATH, "r") as f:
        f_content = f.read()
    assert result.content == f_content


def test_upload_download_image_file():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)
    result = client.upload_file(SAMPLE_IMAGE_PATH, SAMPLE_IMAGE_NAME)
    assert isinstance(result, dm.UploadOutput)
    assert result.message == "succeed"
    assert result.data == f"/mnt/{SAMPLE_IMAGE_NAME}"

    result = client.download_file(SAMPLE_IMAGE_NAME)
    assert isinstance(result, dm.DownloadSuccessOutput)
    with open(SAMPLE_IMAGE_PATH, "rb") as f:
        f_content = f.read()
    assert result.content.encode() == f_content


def test_download_nonexist_file():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)
    result = client.download_file("this_file_should_not_exist")

    assert isinstance(result, dm.ErrorResponse)


def test_heartbeat():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)
    result = client.heartbeat()

    assert isinstance(result, (dm.HeartbeatOutput, dm.ErrorResponse))


def test_refresh_sandbox():
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)
    result = client.refresh_sandbox()

    assert isinstance(result, (dm.RefreshSandboxOutput, dm.ErrorResponse))


# A session scope fixture to ensure the sandbox is refreshed after all tests
@pytest.fixture(scope='session', autouse=True)
def refresh_sandbox_after_all_tests():
    yield
    client = AsyncSandboxClient(SAMPLE_SESSION_ID)
    client.refresh_sandbox()