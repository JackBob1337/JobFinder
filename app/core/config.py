from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    openai_api_key:str | None = None
    apify_api_token: str | None = None

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()