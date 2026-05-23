from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import ShortsClip, ShortsContent


def generate_shorts(analysis: ContentAnalysis) -> ShortsContent:
    clips = []
    for index, idea in enumerate(analysis.key_ideas[:5]):
        start = float(index * 45)
        clips.append(
            ShortsClip(
                title=idea.title[:100],
                start_seconds=start,
                end_seconds=start + 35.0,
                hook=idea.summary[:220],
                script=(
                    f"Open with: {idea.summary} Then show why it matters, give one concrete "
                    f"example, and close with: {analysis.audience_takeaway}"
                ),
            )
        )
    while len(clips) < 3:
        start = float(len(clips) * 45)
        clips.append(
            ShortsClip(
                title="Core takeaway",
                start_seconds=start,
                end_seconds=start + 35.0,
                hook=analysis.hook[:220],
                script=f"Use the hook, explain the tension, and land on {analysis.audience_takeaway}",
            )
        )
    return ShortsContent(clips=clips)

