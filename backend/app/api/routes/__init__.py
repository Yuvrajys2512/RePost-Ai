from fastapi import APIRouter

from app.api.routes import content, history, videos, voice

router = APIRouter()
router.include_router(videos.router, prefix="/videos", tags=["videos"])
router.include_router(content.router, prefix="/content", tags=["content"])
router.include_router(voice.router, prefix="/voice-profile", tags=["voice-profile"])
router.include_router(history.router, prefix="/history", tags=["history"])

