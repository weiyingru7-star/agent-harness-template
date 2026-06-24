from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "agent-harness-api"
    api_host: str = "127.0.0.1"
    api_port: int = 8005

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
