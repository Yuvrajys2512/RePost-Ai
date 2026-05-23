from datetime import UTC, datetime, timedelta

from app.models.user import UserModel

PLAN_LIMITS = {
    "free": 2,
    "starter": 10,
    "pro": 30,
    "agency": 99999,
}


def check_and_reset_quota(user: UserModel) -> None:
    """Resets user quota if billing cycle period of 30 days has passed."""
    now = datetime.now(UTC)
    
    # Normalize datetimes to be timezone-naive to support SQLite compatibly
    now_naive = now.replace(tzinfo=None)
    billing_start_naive = user.billing_cycle_start.replace(tzinfo=None)
    
    if now_naive >= billing_start_naive + timedelta(days=30):
        user.videos_used_this_month = 0
        user.billing_cycle_start = now


def get_plan_limit(plan: str) -> int:
    """Returns the limit of videos allowed per month for a given plan."""
    return PLAN_LIMITS.get(plan.lower(), 2)


def has_remaining_quota(user: UserModel) -> bool:
    """Checks if the user has remaining quota for processing video content."""
    check_and_reset_quota(user)
    limit = get_plan_limit(user.plan)
    return user.videos_used_this_month < limit
