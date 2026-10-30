import os
from pathlib import Path
from pydantic_settings import BaseSettings

try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
    else:
        load_dotenv()
except ImportError:
    pass

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuDiff AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Storage
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    REPORTS_DIR: Path = STORAGE_DIR / "reports"
    
    # Limits
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".md"}
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Default AI Settings
    DEFAULT_PROVIDER: str = os.getenv("DOCUDIFF_LLM_PROVIDER", "deterministic")
    DEFAULT_THRESHOLD: float = 0.65
    USE_LANGGRAPH: bool = True

    model_config = {"case_sensitive": True}

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
