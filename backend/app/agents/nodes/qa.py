"""QA node — runs after all generators.

Checks each platform's output for generic AI phrases and tweet character
overruns. If a platform fails, retries its generator once.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import (
    BlogContent,
    CarouselContent,
    GeneratedContentKit,
    LinkedInContent,
    NewsletterContent,
    ShortsContent,
    TwitterContent,
)
from app.schemas.voice import VoiceStyle

# ---------------------------------------------------------------------------
# Banned-phrase list — phrases that mark AI slop regardless of platform
# ---------------------------------------------------------------------------

_BANNED: frozenset[str] = frozenset(
    [
        "in today's fast-paced world",
        "in today's digital age",
        "in this day and age",
        "let's dive in",
        "delve into",
        "game-changer",
        "game changer",
        "at the end of the day",
        "in conclusion",
        "it's important to note",
        "it is important to note",
        "needless to say",
        "cutting-edge",
        "cutting edge",
        "it goes without saying",
        "in the world of",
        "as we navigate",
        "harness the power",
        "unlock your potential",
        "revolutionize",
        "transformative",
        "paradigm shift",
    ]
)


def _contains_banned(text: str) -> str | None:
    """Return the first banned phrase found in text, or None."""
    lower = text.lower()
    for phrase in _BANNED:
        if phrase in lower:
            return phrase
    return None


# ---------------------------------------------------------------------------
# Per-platform checkers — return list of issue strings (empty = pass)
# ---------------------------------------------------------------------------


def _check_twitter(content: TwitterContent) -> list[str]:
    issues: list[str] = []
    all_tweets = [
        *[(f"standalone[{i}]", t) for i, t in enumerate(content.standalone_tweets)],
        *[(f"thread[{i}]", t) for i, t in enumerate(content.thread)],
    ]
    for label, tweet in all_tweets:
        if len(tweet.text) > 280:
            issues.append(f"tweet {label} is {len(tweet.text)} chars (limit 280)")
        phrase = _contains_banned(tweet.text)
        if phrase:
            issues.append(f"tweet {label} contains banned phrase: '{phrase}'")
    return issues


def _check_linkedin(content: LinkedInContent) -> list[str]:
    issues: list[str] = []
    for i, post in enumerate(content.posts):
        phrase = _contains_banned(post.body)
        if phrase:
            issues.append(f"LinkedIn post[{i}] body contains banned phrase: '{phrase}'")
    return issues


def _check_newsletter(content: NewsletterContent) -> list[str]:
    phrase = _contains_banned(content.body)
    return [f"newsletter body contains banned phrase: '{phrase}'"] if phrase else []


def _check_blog(content: BlogContent) -> list[str]:
    issues: list[str] = []
    for i, section in enumerate(content.sections):
        phrase = _contains_banned(section.body)
        if phrase:
            issues.append(f"blog section[{i}] contains banned phrase: '{phrase}'")
    return issues


def _check_shorts(content: ShortsContent) -> list[str]:
    issues: list[str] = []
    for i, clip in enumerate(content.clips):
        phrase = _contains_banned(clip.script)
        if phrase:
            issues.append(f"Shorts clip[{i}] script contains banned phrase: '{phrase}'")
    return issues


def _check_carousel(content: CarouselContent) -> list[str]:
    issues: list[str] = []
    for i, slide in enumerate(content.slides):
        phrase = _contains_banned(slide.body)
        if phrase:
            issues.append(f"carousel slide[{i}] contains banned phrase: '{phrase}'")
    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class QAResult:
    kit: GeneratedContentKit
    issues: dict[str, list[str]] = field(default_factory=dict)
    retried: set[str] = field(default_factory=set)

    @property
    def passed(self) -> bool:
        return not self.issues


def run_qa(
    kit: GeneratedContentKit,
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> QAResult:
    """Check all platform outputs; retry any that fail once."""
    # Lazy imports avoid circular dependencies and keep startup fast
    from app.agents.nodes.generators.blog import generate_blog
    from app.agents.nodes.generators.carousel import generate_carousel
    from app.agents.nodes.generators.linkedin import generate_linkedin
    from app.agents.nodes.generators.newsletter import generate_newsletter
    from app.agents.nodes.generators.shorts import generate_shorts
    from app.agents.nodes.generators.twitter import generate_twitter

    all_issues: dict[str, list[str]] = {}
    retried: set[str] = set()
    patches: dict[str, object] = {}

    checks: list[tuple[str, object, object, object]] = [
        ("twitter", kit.twitter, _check_twitter, generate_twitter),
        ("linkedin", kit.linkedin, _check_linkedin, generate_linkedin),
        ("newsletter", kit.newsletter, _check_newsletter, generate_newsletter),
        ("blog", kit.blog, _check_blog, generate_blog),
        ("shorts", kit.shorts, _check_shorts, generate_shorts),
        ("carousel", kit.carousel, _check_carousel, generate_carousel),
    ]

    for platform, content, checker, generator in checks:
        issues = checker(content)  # type: ignore[operator]
        if issues:
            all_issues[platform] = issues
            try:
                patches[platform] = generator(analysis, voice_style)  # type: ignore[operator]
                retried.add(platform)
            except Exception:
                # If the retry itself fails, keep the original output
                pass

    if patches:
        kit = kit.model_copy(update=patches)

    return QAResult(kit=kit, issues=all_issues, retried=retried)
