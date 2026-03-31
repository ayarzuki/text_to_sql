from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve .env from project root (parent of backend/)
_env_file = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # GLM API
    GLM_API_KEY: str = ""
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    GLM_MODEL: str = "glm-4"
    GLM_EMBEDDING_MODEL: str = "embedding-3"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/texttosql"

    # RAG
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    RAG_TOP_K: int = 10

    # App
    MAX_RESULT_ROWS: int = 1000
    RATE_LIMIT_PER_MINUTE: int = 20

    model_config = {"env_file": str(_env_file), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
