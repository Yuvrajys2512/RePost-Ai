from __future__ import annotations

import re

from app.schemas.analysis import ContentAnalysis, ContentIdea, StoryBeat
from app.schemas.transcript import Transcript


def analyze_content(transcript: Transcript, *, title: str | None = None) -> ContentAnalysis:
    """Return a deterministic analysis contract until the LLM analyzer is wired."""

    sentences = _sentences(transcript.text)
    if not sentences:
        raise ValueError("Transcript has no analyzable text")

    hook = _first_substantial_sentence(sentences)
    ideas = _extract_ideas(sentences)
    quotes = _extract_quotes(transcript.text, sentences)
    data_points = _extract_data_points(sentences)

    return ContentAnalysis(
        video_id=transcript.video_id,
        title=title,
        summary=_summarize(sentences),
        hook=hook,
        key_ideas=ideas,
        quotes=quotes,
        data_points=data_points,
        emotional_beats=_extract_emotional_beats(sentences),
        story_structure=[
            StoryBeat(label="Hook", description=hook),
            StoryBeat(label="Tension", description=ideas[0].summary),
            StoryBeat(label="Payoff", description=ideas[-1].summary),
        ],
        audience_takeaway=_audience_takeaway(ideas),
    )


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]


def _first_substantial_sentence(sentences: list[str]) -> str:
    for sentence in sentences:
        if len(sentence.split()) >= 8:
            return sentence[:220]
    return sentences[0][:220]


def _summarize(sentences: list[str]) -> str:
    selected = sentences[:3]
    return " ".join(selected)[:700]


def _extract_ideas(sentences: list[str]) -> list[ContentIdea]:
    substantial = [sentence for sentence in sentences if len(sentence.split()) >= 8]
    selected = substantial[:5] or sentences[:1]
    ideas = []
    for index, sentence in enumerate(selected, start=1):
        title = _idea_title(sentence, index)
        ideas.append(
            ContentIdea(
                title=title,
                summary=sentence[:320],
                evidence=[sentence[:220]],
            )
        )
    return ideas


def _idea_title(sentence: str, index: int) -> str:
    words = re.findall(r"[A-Za-z0-9']+", sentence)
    title = " ".join(words[:8]).strip()
    return title or f"Key idea {index}"


def _extract_quotes(text: str, sentences: list[str]) -> list[str]:
    quoted = re.findall(r'"([^"]{12,180})"', text)
    if quoted:
        return quoted[:5]
    return [sentence for sentence in sentences if len(sentence.split()) <= 18][:3]


def _extract_data_points(sentences: list[str]) -> list[str]:
    return [sentence for sentence in sentences if re.search(r"\d", sentence)][:5]


def _extract_emotional_beats(sentences: list[str]) -> list[str]:
    markers = ("struggle", "mistake", "surprise", "fear", "hope", "win", "failed", "learned")
    beats = [sentence for sentence in sentences if any(marker in sentence.lower() for marker in markers)]
    return beats[:5] or ["The transcript introduces a problem, develops tension, and resolves it."]


def _audience_takeaway(ideas: list[ContentIdea]) -> str:
    return f"Use the core insight from '{ideas[0].title}' as the practical takeaway."

