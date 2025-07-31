from pydantic_settings import BaseSettings
from pathlib import Path
import secrets


class Settings(BaseSettings):
    PORT: int
    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_SECONDS: int = 3600  # 1 час

    JWT_REFRESH_EXP_SECONDS: int = 30 * 24 * 3600  # 30 дней
    JWT_REFRESH_SECRET: str = secrets.token_urlsafe(32)

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str

    class Config:
        env_file = str(Path(__file__).parent / ".env")
        env_file_encoding = "utf-8"


settings = Settings()

# import secrets
# print(secrets.token_urlsafe(32))