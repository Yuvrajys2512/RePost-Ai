from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_history(page: int = 1, per_page: int = 20) -> dict:
    return {"videos": [], "total": 0, "page": page, "per_page": per_page}

