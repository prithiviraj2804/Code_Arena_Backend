from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    app_version: str
    base_path: str
    code_arena_api_url: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    postgresql_database_master_url: str
    postgresql_database_slave_url: str

    environment: str

    class Config:
        env_file = ".env"

settings = Settings()