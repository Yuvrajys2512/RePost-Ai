"""Transactional email service via Resend.

All functions are no-ops when RESEND_API_KEY is not configured, so the app
works locally without an API key.
"""
from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

FROM_ADDRESS = "RePost AI <hello@repostai.com>"


def _client():
    import resend

    settings = get_settings()
    if not settings.resend_api_key:
        return None
    resend.api_key = settings.resend_api_key
    return resend


def send_welcome_email(to_email: str, name: str | None = None) -> None:
    """Sent immediately after a new user signs up."""
    resend = _client()
    if not resend:
        logger.debug("Resend not configured — skipping welcome email to %s", to_email)
        return

    display_name = name or to_email.split("@")[0]
    html = f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
  <h1 style="font-size:22px;font-weight:700;margin-bottom:8px">
    Welcome to RePost AI, {display_name}.
  </h1>
  <p style="color:#555;margin-bottom:16px">
    You can now paste any YouTube URL and get a full content kit in under 60 seconds —
    Twitter threads, LinkedIn posts, newsletters, blog posts, Shorts scripts, and carousels.
  </p>

  <p style="font-weight:600;margin-bottom:6px">Here's what to do first:</p>
  <ol style="padding-left:20px;color:#555;line-height:1.8">
    <li>Open the dashboard and paste a YouTube URL you've been meaning to repurpose.</li>
    <li>Hit Generate and watch the pipeline run.</li>
    <li>Copy the Twitter thread and post it. That's it.</li>
  </ol>

  <p style="margin-top:20px;color:#555">
    On the free tier you get 3 videos per month.
    If you hit the limit and want more — upgrade inside the dashboard.
  </p>

  <p style="margin-top:20px;color:#555">
    If anything breaks or the output quality isn't there yet, reply to this email and
    tell me exactly what happened. I read every reply.
  </p>

  <p style="margin-top:24px">— Yuvraj, founder of RePost AI</p>
</div>
"""

    try:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [to_email],
            "subject": "You're in — here's how to get your first content kit",
            "html": html,
        })
        logger.info("Welcome email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send welcome email to %s", to_email)


def send_payment_confirmation(
    to_email: str,
    plan: str,
    name: str | None = None,
) -> None:
    """Sent when a subscription is created or upgraded."""
    resend = _client()
    if not resend:
        logger.debug("Resend not configured — skipping payment confirmation to %s", to_email)
        return

    plan_limits = {"starter": "10", "pro": "30", "agency": "unlimited"}
    limit = plan_limits.get(plan.lower(), "30")
    display_name = name or to_email.split("@")[0]
    plan_display = plan.capitalize()

    html = f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
  <h1 style="font-size:22px;font-weight:700;margin-bottom:8px">
    You're on {plan_display}. Thank you, {display_name}.
  </h1>
  <p style="color:#555;margin-bottom:16px">
    Your plan is active. You can now process <strong>{limit} videos per month</strong>.
  </p>

  <p style="color:#555;margin-bottom:16px">
    Everything you generated before is still in your history.
    Head back to the dashboard and keep going.
  </p>

  <p style="color:#555">
    Questions about your subscription? Reply here — I'll sort it out personally.
  </p>

  <p style="margin-top:24px">— Yuvraj, founder of RePost AI</p>
</div>
"""

    try:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [to_email],
            "subject": f"Payment confirmed — you're on {plan_display}",
            "html": html,
        })
        logger.info("Payment confirmation sent to %s (plan: %s)", to_email, plan)
    except Exception:
        logger.exception("Failed to send payment confirmation to %s", to_email)


def send_failed_payment_email(to_email: str, name: str | None = None) -> None:
    """Sent when a subscription payment fails."""
    resend = _client()
    if not resend:
        logger.debug("Resend not configured — skipping failed payment email to %s", to_email)
        return

    display_name = name or to_email.split("@")[0]

    html = f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
  <h1 style="font-size:22px;font-weight:700;margin-bottom:8px">
    Payment issue on your RePost AI account
  </h1>
  <p style="color:#555;margin-bottom:16px">
    Hi {display_name} — your most recent payment didn't go through.
    Your account has been moved to the free tier until the payment is resolved.
  </p>

  <p style="color:#555;margin-bottom:16px">
    To fix this, update your payment method in the billing section of your dashboard
    and retry the charge.
  </p>

  <p style="color:#555">
    If you think this is a mistake or need help, just reply here.
  </p>

  <p style="margin-top:24px">— Yuvraj, founder of RePost AI</p>
</div>
"""

    try:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [to_email],
            "subject": "Action needed: payment issue on your RePost AI account",
            "html": html,
        })
        logger.info("Failed payment email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send failed-payment email to %s", to_email)
