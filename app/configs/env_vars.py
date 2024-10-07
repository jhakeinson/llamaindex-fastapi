from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentVarSettings(BaseSettings):
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env")
