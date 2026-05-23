from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import CarouselContent, CarouselSlide


def generate_carousel(analysis: ContentAnalysis) -> CarouselContent:
    slides = [
        CarouselSlide(
            slide_number=1,
            headline=analysis.hook[:90],
            body="A strong carousel starts by making one specific promise.",
        )
    ]
    for idea in analysis.key_ideas[:6]:
        slides.append(
            CarouselSlide(
                slide_number=len(slides) + 1,
                headline=idea.title[:90],
                body=idea.summary[:220],
            )
        )
    slides.append(
        CarouselSlide(
            slide_number=len(slides) + 1,
            headline="The takeaway",
            body=analysis.audience_takeaway[:220],
        )
    )
    while len(slides) < 6:
        slides.insert(
            -1,
            CarouselSlide(
                slide_number=len(slides),
                headline="Make it specific",
                body="Specific ideas travel farther than broad summaries.",
            ),
        )
        for index, slide in enumerate(slides, start=1):
            slide.slide_number = index

    return CarouselContent(
        title=analysis.hook[:100],
        slides=slides[:10],
        caption=f"Save this if you want to repurpose videos without flattening the story. {analysis.audience_takeaway}",
    )
