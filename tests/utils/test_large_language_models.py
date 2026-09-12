import pytest
from ops_pilot.utils.large_language_models import load_llm
from ops_pilot.config.settings import lookup_for_setting
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

@pytest.fixture
def mock_llm_config(monkeypatch):
    mock_config = {
        "llm": {
            "provider": "openai",
            "openai": {
                "model_name": "gpt-4o-mini",
                "temperature": 0.5
            },
            "gemini": {
                "model_name": "gemini-1.5-flash",
                "temperature": 0.7
            }
        },
        "env_openai_api_key": "test_openai_key",
        "env_gemini_api_key": "test_gemini_key"
    }
    
    # We need to mock the get behavior of lookup_for_setting.config
    # Since lookup_for_setting is a dictionary-like object via __getitem__,
    # and it uses self.config, we can just replace the whole dict.
    monkeypatch.setattr(lookup_for_setting, "config", mock_config)
    return mock_config

def test_load_llm_openai_default(mock_llm_config):
    llm = load_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0.5

def test_load_llm_openai_explicit(mock_llm_config):
    llm = load_llm(provider="openai")
    assert isinstance(llm, ChatOpenAI)

def test_load_llm_gemini(mock_llm_config):
    llm = load_llm(provider="gemini")
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model == "gemini-1.5-flash"
    assert llm.temperature == 0.7

def test_load_llm_missing_openai_key(mock_llm_config, monkeypatch):
    monkeypatch.setitem(mock_llm_config, "env_openai_api_key", None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        load_llm(provider="openai")

def test_load_llm_missing_gemini_key(mock_llm_config, monkeypatch):
    monkeypatch.setitem(mock_llm_config, "env_gemini_api_key", None)
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
        load_llm(provider="gemini")

def test_load_llm_invalid_provider(mock_llm_config):
    with pytest.raises(ValueError, match="Unsupported provider : invalid"):
        load_llm(provider="invalid")
