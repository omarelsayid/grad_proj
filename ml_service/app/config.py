import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "skillsync_db")
    DB_USER: str = os.getenv("DB_USER", "skillsync")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "skillsync_password")
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./app/models")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
