from uuid import UUID

from fastapi import APIRouter

router = APIRouter()


@router.get("/{content_id}")
async def get_content(content_id: UUID) -> dict:
    return {"content_id": content_id, "status": "not_implemented"}

