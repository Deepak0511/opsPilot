# Load LLM models from the settings configuration.
from ops_pilot.config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Utility to load the configured LLM
def load_llm(provider=None):

    # Focus on the LLM configuration section only.
    llm_config = settings["llm"]

    if provider is None:
        provider = llm_config["provider"].lower()

    #provider = provider.lower()

    if provider == "openai":
        api_key = settings["env_openai_api_key"]
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add OPENAI_API_KEY=your-api-key in the environment."
            )

        return ChatOpenAI(
            model=llm_config["openai"]["model_name"],
            temperature=llm_config["openai"].get("temperature", 0),
            api_key=api_key
        )

    elif provider == "gemini":
        api_key = settings["env_gemini_api_key"]
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add GEMINI_API_KEY=your-api-key in the environment."
            )

        return ChatGoogleGenerativeAI(
            model=llm_config["gemini"]["model_name"],
            temperature=llm_config["gemini"].get("temperature", 0),
            google_api_key=api_key
        )

    else:

        raise ValueError(
            f"Unsupported provider : {provider}"
        )