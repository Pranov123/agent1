from openai import OpenAI
import config

def get_client() -> OpenAI:
    """Returns the right client based on config.PROVIDER"""
    if config.PROVIDER == "groq":
        return OpenAI(
            base_url=config.GROQ_BASE_URL,
            api_key=config.GROQ_API_KEY,
            timeout=config.REQUEST_TIMEOUT
        )
    else:
        return OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key="ollama",
            timeout=config.REQUEST_TIMEOUT
        )

def get_primary_model() -> str:
    if config.PROVIDER == "groq":
        return config.GROQ_PRIMARY_MODEL
    return config.OLLAMA_PRIMARY_MODEL

def get_validation_model() -> str:
    if config.PROVIDER == "groq":
        return config.GROQ_VALIDATION_MODEL
    return config.OLLAMA_VALIDATION_MODEL