from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    app_name: str = "Personal Job Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production-please"
    api_prefix: str = "/api/v1"

    # Single user ID (fixed — this is a single-user application)
    single_user_id: str = "00000000-0000-0000-0000-000000000001"

    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent"
    # Sync URL for Celery workers (no asyncpg)
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/job_agent"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ── Redis / Celery ────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── LLM ──────────────────────────────────────────────────
    # Cost budget: ₹1000/month (~$12). Use Haiku for all routine tasks.
    # Sonnet only for resume/cover-letter writing (max 3/day).
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_primary_provider: str = "anthropic"
    llm_primary_model: str = "claude-haiku-4-5-20251001"   # cheap: $0.80/MTok in
    llm_quality_model: str = "claude-sonnet-4-6"            # quality: resume/outreach only
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    llm_fallback_provider: str = "openai"
    llm_fallback_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 1024                              # keep responses short
    llm_temperature: float = 0.3
    # Daily LLM budget guard (approx tokens)
    llm_max_daily_tokens: int = 400_000                    # ~$0.40/day = $12/month

    # ── Embeddings / Vector ───────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ── MinIO / Storage ───────────────────────────────────────
    # minio_endpoint = "host:port" (no scheme)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_resumes: str = "resumes"
    minio_secure: bool = False

    # ── Email ─────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    notification_email: str = ""

    # ── Scraping ──────────────────────────────────────────────
    scraper_download_delay: float = 2.0
    scraper_max_concurrent: int = 4
    scraper_respect_robots: bool = True

    # ── Job matching ──────────────────────────────────────────
    match_score_threshold: int = 50
    high_match_threshold: int = 75

    # ── Admin credentials (single-user login) ─────────────────
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme"

    # ── Flower monitoring ─────────────────────────────────────
    flower_user: str = "admin"
    flower_password: str = "admin"

    # ── Application limits ────────────────────────────────────
    max_daily_applies: int = 5        # auto-applies per day (5/day = ~100/month)
    max_monthly_applies: int = 100    # hard monthly cap
    prefer_india_first: bool = True   # apply India jobs before international
    max_daily_pipelines: int = 30     # LLM pipeline runs per day (cost control)

    # ── Feature flags ─────────────────────────────────────────
    enable_email_notifications: bool = False
    enable_qdrant: bool = True
    enable_minio: bool = True
    enable_llm: bool = True

    @property
    def user_id(self) -> str:
        return self.single_user_id


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
