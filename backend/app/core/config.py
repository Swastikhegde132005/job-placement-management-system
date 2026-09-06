from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PlacementHub"
    DATABASE_URL: str = "postgresql+asyncpg://hub_user:hub_password@localhost:5432/placement_hub"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "placement-hub-ultra-secure-random-token-secret-key-1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
