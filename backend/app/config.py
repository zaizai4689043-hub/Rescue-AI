from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-change-in-production"
    DATABASE_URL: str = "sqlite:///./aidisaster.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    # DashScope（通义千问）真实AI接入：无密钥时所有AI功能自动降级为预设/规则引擎
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_TEXT_MODEL: str = "qwen3.8-max"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        # .env 里可能混入其他模块的键（如 dashscope_*），容忍而非拒绝，
        # 否则 pydantic-settings 会因 extra_forbidden 导致整个应用无法启动。
        "extra": "ignore",
    }


settings = Settings()
