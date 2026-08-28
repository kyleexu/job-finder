"""配置管理"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Job Finder"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model_id: str = "deepseek-v4-flash"

    jsearch_api_key: str = ""
    jsearch_base_url: str = "https://api.openwebninja.com/jsearch"
    jsearch_timeout: float = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


def get_settings() -> Settings:
    return settings
