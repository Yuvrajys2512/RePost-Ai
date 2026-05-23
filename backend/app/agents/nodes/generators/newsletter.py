from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import NewsletterContent


def generate_newsletter(analysis: ContentAnalysis) -> NewsletterContent:
    first_idea = analysis.key_ideas[0]
    subject_seed = first_idea.title[:42].rstrip()
    body = (
        f"{analysis.hook}\n\n"
        f"The important idea is this: {first_idea.summary}\n\n"
        f"The structure matters because the video does not just list information. It creates "
        f"a hook, gives the audience a reason to care, and turns the insight into a practical "
        f"next step.\n\n"
        f"{analysis.audience_takeaway}"
    )
    return NewsletterContent(
        subject_lines=[
            f"The mistake behind {subject_seed}",
            f"A sharper way to use {subject_seed}",
            "Turn one video into better ideas",
        ],
        preview_text=analysis.audience_takeaway[:180],
        body=body,
        cta="Watch the full video and look for the hook, tension, insight, and payoff.",
    )

