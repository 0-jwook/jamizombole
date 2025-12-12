"""설정 관리 모듈"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path


# 프로젝트 루트 경로 (src 디렉토리)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    google_api_key: str = ""  # Google Gemini API 키
    tourism_api_key: str = ""  # 공공데이터포털 API 키

    # API URLs
    tourism_api_url: str = "https://apis.data.go.kr/B551011/KorService2/searchKeyword2"

    # LLM Settings
    gemini_model: str = "gemini-1.5-flash"
    temperature: float = 0.7
    
    # RAG Settings
    chroma_persist_directory: str = str(BASE_DIR / "app" / "db" / "chroma_db")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()

