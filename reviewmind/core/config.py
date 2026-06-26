from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    # Phase 2
    github_token: str = ""
    github_api_version: str = "2022-11-28"
    github_rate_limit_warning: int = 100  # warn when remaining drops below this
    github_request_timeout: float = 10.0


settings = Settings()
