from openai import OpenAI
import config

def get_client() -> OpenAI:
    return OpenAI(
        base_url=config.GROQ_BASE_URL,
        api_key=config.GROQ_API_KEY,
        timeout=config.REQUEST_TIMEOUT
    )

def get_primary_model() -> str:
    return config.GROQ_PRIMARY_MODEL

def get_validation_model() -> str:
    return config.GROQ_VALIDATION_MODEL