from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Platform(StrEnum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


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


class GeneratedContentKit(BaseModel):
    twitter: TwitterContent
    linkedin: LinkedInContent

