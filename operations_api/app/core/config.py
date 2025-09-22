"""
Operations API Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RFID Operations API"
    API_PORT: int = 8443
    API_HOST: str = "0.0.0.0"

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "rfid_operations_db")
    DB_USER: str = os.getenv("DB_USER", "rfid_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "rfid123!")

    # Manager Database (for sync)
    MANAGER_DB_NAME: str = os.getenv("MANAGER_DB_NAME", "rfid_inventory")
    MANAGER_DB_USER: str = os.getenv("MANAGER_DB_USER", "rfid_user")
    MANAGER_DB_PASSWORD: str = os.getenv("MANAGER_DB_PASSWORD", "rfid123!")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "1"))

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://localhost:3000",
        f"https://{os.getenv('TAILSCALE_IP', '100.103.67.41')}:443",
        f"https://{os.getenv('TAILSCALE_IP', '100.103.67.41')}:8443",
        "http://localhost:8101",
    ]

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def MANAGER_DATABASE_URL(self) -> str:
        return f"mysql+mysqlconnector://{self.MANAGER_DB_USER}:{self.MANAGER_DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.MANAGER_DB_NAME}"

    class Config:
        case_sensitive = True

settings = Settings()