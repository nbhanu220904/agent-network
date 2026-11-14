from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')
    database_url: str
    redis_url: str
    gemini_api_key: str
    # gemini_chat_model: str = 'gemini-2.5-flash'
    # gemini_chat_model: str = 'gemini-3.5-flash-lite'
    gemini_chat_model: str = 'gemini-3.8-flash'
    cohere_api_key: str = ''
    api_base_url: str = 'http://localhost:8000'
    top_k: int = 50
    max_notify: int = 5
    final_threshold: float = 0.75
    vector_only_threshold: float = 0.60
    registration_token: str = ''

settings = Settings()