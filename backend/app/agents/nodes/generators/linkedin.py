from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import LinkedInContent, LinkedInPost


def generate_linkedin(analysis: ContentAnalysis) -> LinkedInContent:
    first_idea = analysis.key_ideas[0]
    second_idea = analysis.key_ideas[min(1, len(analysis.key_ideas) - 1)]

    posts = [
        LinkedInPost(
            hook=_hook_line(analysis.hook),
            body=_body_from_analysis(analysis, first_idea.summary),
            cta="What would you apply from this in your own content workflow?",
        ),
        LinkedInPost(
            hook=f"Most creators miss this: {first_idea.title}",
            body=_body_from_analysis(analysis, second_idea.summary),
            cta="Where do you see this pattern showing up in your niche?",
        ),
    ]
    return LinkedInContent(posts=posts)


def _hook_line(hook: str) -> str:
    clean = " ".join(hook.split())
    return clean[:217] + "..." if len(clean) > 220 else clean


def _body_from_analysis(analysis: ContentAnalysis, lead: str) -> str:
    data = f" One concrete signal: {analysis.data_points[0]}" if analysis.data_points else ""
    takeaway = analysis.audience_takeaway.rstrip(".")
    return (
        f"{lead} The useful part is not just the point itself, but the structure behind it: "
        f"the content creates a clear hook, builds tension around a specific problem, and lands "
        f"on a practical payoff. {takeaway}.{data} That gives the audience "
        f"something specific to remember and something simple to act on after watching."
    )
