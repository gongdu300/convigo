from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API 설정
    OPENAI_API_KEY: str 
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    ALGORITHM: str = "HS256"
    PROJECT_NAME: str = "편의점 행사상품 크롤링 서비스"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()