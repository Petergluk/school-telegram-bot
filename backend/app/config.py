from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "school-mvp"
    database_url: str = "sqlite:///./school.db"
    secret_key: str = "change_me_super_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
