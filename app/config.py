from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int
    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_SECONDS: int = 3600

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# import secrets
# print(secrets.token_urlsafe(32))