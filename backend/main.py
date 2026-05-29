from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.rate_limit import RateLimitMiddleware
from app.services.index import get_retrieval_index
from app.utils.config import settings
from app.utils.logger import setup_logger
from routes.chat import router as chat_router
from routes.health import router as health_router

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup
    logger.info("Starting up Docling Assistant API")
    try:
        # Initialize retrieval index on startup
        index = get_retrieval_index()
        logger.info(f"Retrieval index initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize retrieval index: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Docling Assistant API")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "name": "Docling Assistant API",
        "status": "ok",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "chat_url": "/api/chat",
    }

# Made with Bob
