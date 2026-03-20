from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.core.config import settings
from backend.core.logging import setup_logging, get_logger
from backend.core.exceptions import AppError, app_error_handler, generic_error_handler
from backend.api.router import api_router

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("Personal Job Agent starting up", version=settings.app_version)
    yield
    log.info("Personal Job Agent shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://networknimble.info",
        "https://www.networknimble.info",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["meta"])
async def health_check():
    return {"status": "ok", "version": settings.app_version}
