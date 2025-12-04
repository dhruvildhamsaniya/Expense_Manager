from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_FOLDER: str = "uploads/receipts"
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    
    class Config:
        env_file = ".env"

settings = Settings()
