from setuptools import setup, find_packages

setup(
    name='infiagent',
    version='0.1.0',
    author='InfiAgent',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    url='https://github.com/InfiAgent/ADA-Agent',
    license='LICENSE.txt',
    description='An awesome package for InfiAgent.',
    long_description=open('README.md').read(),
    package_data={
        'infiagent.configs.agent_configs': ['*.yaml'],
        'infiagent.configs.tool_configs': ['*.yaml'],
    },
    install_requires=[
        "streamlit",
        "pyyaml",
        "pytest",
        "openai==0.27.7",
        "fastapi",
        "uvicorn",
        "uvloop",
        "watchdog",
        "chardet",
        "werkzeug",
        "python-dotenv",
        "motor",
        "aiofiles",
        "sse_starlette",
        "loguru",
        "jupyter_client",
        "pandas",
        "scikit-learn",
        "scipy",
        "ipykernel"
    ],
    python_requires='>=3.9'
)
