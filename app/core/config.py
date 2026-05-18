from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # DashScope API (通义千问)
    DASHSCOPE_API_KEY: str
    API_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Model Configuration
    MODEL_NAME: str = "qwen3.5-omni-flash"
    MAX_IMAGE_SIZE: int = 1024

    # RAG Configuration
    TAGGING_MODEL_NAME: str = "qwen-vl-plus"
    EMBEDDING_MODEL_NAME: str = "text-embedding-v3"
    CHROMA_DB_PATH: str = "./data/chroma_db"
    RAG_SIMILARITY_THRESHOLD: float = 0.55

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:3000",
        "null"  # 允许 file:// 协议访问
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
