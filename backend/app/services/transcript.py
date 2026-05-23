from __future__ import annotations

import re
from typing import Protocol
from urllib.parse import parse_qs, urlparse

from app.schemas.transcript import Transcript, TranscriptSegment


class TranscriptExtractionError(RuntimeError):
    """Raised when transcript extraction cannot produce a transcript."""


class TranscriptProvider(Protocol):
    def fetch(self, video_id: str, source_url: str) -> Transcript:
        """Fetch a transcript for a YouTube video."""


class YouTubeTranscriptApiProvider:
    """Transcript provider backed by optional youtube-transcript-api dependency."""

    def fetch(self, video_id: str, source_url: str) -> Transcript:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError as exc:
            raise TranscriptExtractionError(
                "youtube-transcript-api is not installed; install it to fetch real transcripts"
            ) from exc

        raw_segments = YouTubeTranscriptApi.get_transcript(video_id)
        segments = [
            TranscriptSegment(
                start_seconds=float(segment["start"]),
                duration_seconds=float(segment["duration"]),
                text=segment["text"],
            )
            for segment in raw_segments
            if segment.get("text")
        ]
        if not segments:
            raise TranscriptExtractionError(f"No transcript segments found for {video_id}")
        return Transcript(video_id=video_id, source_url=source_url, segments=segments)


class TranscriptService:
    def __init__(self, provider: TranscriptProvider | None = None) -> None:
        self.provider = provider or YouTubeTranscriptApiProvider()

    def extract(self, youtube_url: str) -> Transcript:
        video_id = extract_youtube_video_id(youtube_url)
        return self.provider.fetch(video_id=video_id, source_url=youtube_url)


def extract_youtube_video_id(youtube_url: str) -> str:
    parsed = urlparse(youtube_url)
    host = parsed.netloc.lower()

    if host.endswith("youtu.be"):
        video_id = parsed.path.strip("/").split("/")[0]
    elif "youtube.com" in host:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/")):
            video_id = parsed.path.strip("/").split("/")[1]
        else:
            video_id = ""
    else:
        video_id = ""

    if not re.fullmatch(r"[\w-]{6,}", video_id):
        raise ValueError("Expected a valid YouTube URL with a video id")
    return video_id


def transcript_from_text(
    text: str,
    *,
    video_id: str = "manual",
    source_url: str = "manual://transcript",
) -> Transcript:
    clean_text = " ".join(text.split())
    if not clean_text:
        raise ValueError("Transcript text cannot be empty")

    words = clean_text.split()
    chunk_size = 45
    segments = []
    for index in range(0, len(words), chunk_size):
        chunk = " ".join(words[index : index + chunk_size])
        segment_number = index // chunk_size
        segments.append(
            TranscriptSegment(
                start_seconds=segment_number * 15.0,
                duration_seconds=15.0,
                text=chunk,
            )
        )

    return Transcript(video_id=video_id, source_url=source_url, segments=segments)

