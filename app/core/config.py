from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Keepr"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Marketplace de contratación de arqueros para partidos amateur"
    ALLOWED_ORIGINS: list[str] = ["*"]
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
