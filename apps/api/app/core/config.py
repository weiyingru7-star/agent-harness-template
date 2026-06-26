from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "agent-harness-api"
    api_host: str = "127.0.0.1"
    api_port: int = 8005
    ai_provider: str = "mock"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_timeout: float = 30
    ai_max_attempts: int = 1
    ai_fallback_provider: str = "mock"
    ai_streaming_enabled: bool = True
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = ""
    openai_compatible_model: str = "gpt-4o-mini"
    local_storage_dir: str = "data/uploads"
    database_url: str = "postgresql://agent_harness:agent_harness@localhost:15432/agent_harness"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context: object) -> None:
        if not self.ai_base_url and self.openai_compatible_base_url:
            self.ai_base_url = self.openai_compatible_base_url
        if not self.ai_api_key and self.openai_compatible_api_key:
            self.ai_api_key = self.openai_compatible_api_key
        if self.ai_model == "gpt-4o-mini" and self.openai_compatible_model:
            self.ai_model = self.openai_compatible_model


settings = Settings()
