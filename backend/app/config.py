from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Existing settings
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_FOLDER: str = "uploads/receipts"
    MAX_UPLOAD_SIZE: int = 5242880
    
    # NEW: OCR Settings
    TESSERACT_CMD: Optional[str] = None  # Path to tesseract executable if not in PATH
    OCR_ENABLED: bool = True
    
    # NEW: Currency API Settings
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest"
    CACHE_EXCHANGE_RATES_HOURS: int = 24
    
    # NEW: Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    EMAIL_ENABLED: bool = True
    
    # NEW: Notification Settings
    BUDGET_WARNING_THRESHOLD: float = 80.0  # Warn at 80%
    BUDGET_ALERT_THRESHOLD: float = 100.0   # Alert at 100%
    
    class Config:
        env_file = ".env"

settings = Settings()