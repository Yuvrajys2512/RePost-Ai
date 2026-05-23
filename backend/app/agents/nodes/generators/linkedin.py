from __future__ import annotations

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import LinkedInContent, LinkedInPost
from app.schemas.voice import VoiceStyle


def generate_linkedin(
    analysis: ContentAnalysis, voice_style: VoiceStyle | None = None
) -> LinkedInContent:
    first_idea = analysis.key_ideas[0]
    second_idea = analysis.key_ideas[min(1, len(analysis.key_ideas) - 1)]

    cta1 = _voice_cta("What would you apply from this in your own content workflow?", voice_style)
    cta2 = _voice_cta("Where do you see this pattern showing up in your niche?", voice_style)

    posts = [
        LinkedInPost(
            hook=_hook_line(analysis.hook),
            body=_body_from_analysis(analysis, first_idea.summary, voice_style),
            cta=cta1,
        ),
        LinkedInPost(
            hook=f"Most creators miss this: {first_idea.title}",
            body=_body_from_analysis(analysis, second_idea.summary, voice_style),
            cta=cta2,
        ),
    ]
    return LinkedInContent(posts=posts)


def _hook_line(hook: str) -> str:
    clean = " ".join(hook.split())
    return clean[:217] + "..." if len(clean) > 220 else clean


def _voice_cta(default: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return default
    tone = voice_style.tone
    if tone == "direct and contrarian":
        return "Disagree? Let me know below."
    if tone == "practical and instructional":
        return "Try this with your next video and share what you find."
    if tone == "reflective and narrative":
        return "What moment shifted how you think about this?"
    return default


def _body_from_analysis(
    analysis: ContentAnalysis, lead: str, voice_style: VoiceStyle | None
) -> str:
    data = f" One concrete signal: {analysis.data_points[0]}" if analysis.data_points else ""
    takeaway = analysis.audience_takeaway.rstrip(".")

    # Inject top vocabulary words if a voice style is provided
    vocab_note = ""
    if voice_style and voice_style.vocabulary:
        keywords = ", ".join(voice_style.vocabulary[:3])
        vocab_note = f" The key ideas here revolve around: {keywords}."

    return (
        f"{lead} The useful part is not just the point itself, but the structure behind it: "
        f"the content creates a clear hook, builds tension around a specific problem, and lands "
        f"on a practical payoff. {takeaway}.{data}{vocab_note} That gives the audience "
        f"something specific to remember and something simple to act on after watching."
    )
