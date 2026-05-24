import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.routes import router as api_router
from app.config import get_settings
from app.db.session import init_db

logger = logging.getLogger(__name__)


def _init_sentry(dsn: str, environment: str) -> None:
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )
    logger.info("Sentry initialized (environment=%s)", environment)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    if settings.sentry_dsn:
        _init_sentry(settings.sentry_dsn, settings.environment)

    if settings.anthropic_api_key:
        logger.info("AI provider: Claude (Anthropic)")
    elif settings.groq_api_key:
        logger.info("AI provider: Groq / Llama 3.3 70B — free tier")
    elif settings.google_api_key:
        logger.info("AI provider: Gemini (Google) — free tier")
    else:
        logger.warning(
            "No AI provider key found (ANTHROPIC_API_KEY, GROQ_API_KEY, or GOOGLE_API_KEY). "
            "Pipeline will use the deterministic fallback. Add a key to backend/.env."
        )
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="RePost AI API",
        version="0.1.0",
        description="API for repurposing YouTube videos into platform-native content.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()

