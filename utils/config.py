import os
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, AnyUrl

load_dotenv()

class Settings(BaseSettings):
    # Основные настройки
    APP_NAME: str = "DataRex"
    DEBUG: bool = Field(False, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    STORAGE_PATH: str = "storage"
    
    # Настройки GigaChain
    GIGA_API_KEY: str = Field(..., env="GIGA_API_KEY")
    GIGA_MODEL: str = "GigaChat:latest"
    GIGA_TEMPERATURE: float = 0.7
    GIGA_TOP_P: float = 0.85
    GIGA_MAX_TOKENS: int = 1024
    
    # Настройки YandexGPT
    YANDEX_API_KEY: str = Field(..., env="YANDEX_API_KEY")
    YANDEX_FOLDER_ID: str = Field(..., env="YANDEX_FOLDER_ID")
    YANDEX_VISION_API_KEY: str = Field(..., env="YANDEX_VISION_API_KEY")
    YANDEX_TEMPERATURE: float = 0.6
    YANDEX_TOP_P: float = 0.9
    YANDEX_MAX_TOKENS: int = 2048
    
    # Базы данных
    REDIS_URL: AnyUrl = Field("redis://localhost:6379/0", env="REDIS_URL")
    DATABASE_URL: str = Field("sqlite:///storage/database.db", env="DATABASE_URL")
    
    # Ограничения
    MAX_CONTEXT_TOKENS: int = 8000
    MAX_FILE_SIZE_MB: int = 20
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()