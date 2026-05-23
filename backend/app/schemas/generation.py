from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Platform(StrEnum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    NEWSLETTER = "newsletter"
    BLOG = "blog"
    SHORTS = "shorts"
    CAROUSEL = "carousel"


class TwitterTweet(BaseModel):
    text: str = Field(min_length=1, max_length=280)


class TwitterContent(BaseModel):
    platform: Platform = Platform.TWITTER
    standalone_tweets: list[TwitterTweet] = Field(min_length=5)
    thread: list[TwitterTweet] = Field(min_length=5)


class LinkedInPost(BaseModel):
    hook: str = Field(min_length=1, max_length=220)
    body: str = Field(min_length=1)
    cta: str = Field(min_length=1, max_length=220)

    @field_validator("body")
    @classmethod
    def body_should_have_substance(cls, value: str) -> str:
        if len(value.split()) < 25:
            raise ValueError("LinkedIn post body must contain at least 25 words")
        return value

    @property
    def text(self) -> str:
        return f"{self.hook}\n\n{self.body}\n\n{self.cta}"


class LinkedInContent(BaseModel):
    platform: Platform = Platform.LINKEDIN
    posts: list[LinkedInPost] = Field(min_length=2, max_length=3)


class NewsletterContent(BaseModel):
    platform: Platform = Platform.NEWSLETTER
    subject_lines: list[str] = Field(min_length=3, max_length=5)
    preview_text: str = Field(min_length=1, max_length=180)
    body: str = Field(min_length=1)
    cta: str = Field(min_length=1, max_length=220)


class BlogSection(BaseModel):
    heading: str = Field(min_length=1, max_length=140)
    body: str = Field(min_length=1)


class BlogContent(BaseModel):
    platform: Platform = Platform.BLOG
    title: str = Field(min_length=1, max_length=120)
    meta_description: str = Field(min_length=1, max_length=160)
    introduction: str = Field(min_length=1)
    sections: list[BlogSection] = Field(min_length=3)
    conclusion: str = Field(min_length=1)


class ShortsClip(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    hook: str = Field(min_length=1, max_length=220)
    script: str = Field(min_length=1)

    @field_validator("end_seconds")
    @classmethod
    def end_should_be_after_start(cls, value: float, info) -> float:
        start = info.data.get("start_seconds")
        if start is not None and value <= start:
            raise ValueError("end_seconds must be greater than start_seconds")
        return value


class ShortsContent(BaseModel):
    platform: Platform = Platform.SHORTS
    clips: list[ShortsClip] = Field(min_length=3, max_length=5)


class CarouselSlide(BaseModel):
    slide_number: int = Field(ge=1)
    headline: str = Field(min_length=1, max_length=90)
    body: str = Field(min_length=1, max_length=220)


class CarouselContent(BaseModel):
    platform: Platform = Platform.CAROUSEL
    title: str = Field(min_length=1, max_length=100)
    slides: list[CarouselSlide] = Field(min_length=6, max_length=10)
    caption: str = Field(min_length=1)


class GeneratedContentKit(BaseModel):
    twitter: TwitterContent
    linkedin: LinkedInContent
    newsletter: NewsletterContent
    blog: BlogContent
    shorts: ShortsContent
    carousel: CarouselContent
