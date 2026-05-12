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

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
