import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def clean_env_keys():
    """Ensure Gemini and OpenAI API keys are not present in test environment to guarantee fast, offline test runs."""
    gemini_val = os.environ.pop("GEMINI_API_KEY", None)
    openai_val = os.environ.pop("OPENAI_API_KEY", None)
    yield
    if gemini_val is not None:
        os.environ["GEMINI_API_KEY"] = gemini_val
    if openai_val is not None:
        os.environ["OPENAI_API_KEY"] = openai_val
