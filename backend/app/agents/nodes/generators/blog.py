from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import BlogContent, BlogSection


def generate_blog(analysis: ContentAnalysis) -> BlogContent:
    sections = [
        BlogSection(
            heading=idea.title,
            body=(
                f"{idea.summary} This works because the point is specific enough to become "
                f"a reusable content angle instead of a generic summary."
            ),
        )
        for idea in analysis.key_ideas[:4]
    ]
    while len(sections) < 3:
        sections.append(
            BlogSection(
                heading="What creators should do next",
                body=analysis.audience_takeaway,
            )
        )

    return BlogContent(
        title=(analysis.title or analysis.hook)[:120],
        meta_description=analysis.summary[:160],
        introduction=(
            f"{analysis.summary} The real value is in translating that structure into "
            f"platform-native content."
        ),
        sections=sections,
        conclusion=f"Bottom line: {analysis.audience_takeaway}",
    )

