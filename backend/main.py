import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure app and ai-engine modules are discoverable
BASE_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = BASE_DIR.parent / "ai-engine"
APP_DIR = BASE_DIR / "app"

for p in [str(BASE_DIR), str(APP_DIR), str(AI_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.config import settings
from app.api.endpoints import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Document Comparison & Change Analyzer API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Welcome to DocuDiff AI API",
        "health_check": f"{settings.API_V1_PREFIX}/health",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

