from __future__ import annotations

import re
from typing import Any

from app.config import get_settings
from app.schemas.analysis import ContentAnalysis, ContentIdea, StoryBeat
from app.schemas.transcript import Transcript

# ---------------------------------------------------------------------------
# Tool definition — forces Claude to return structured JSON matching the
# ContentAnalysis schema instead of free-form prose.
# ---------------------------------------------------------------------------

_ANALYSIS_TOOL: dict[str, Any] = {
    "name": "content_analysis",
    "description": "Output the structured content analysis of a YouTube video transcript.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": (
                    "2-3 sentences. What is this video fundamentally about — "
                    "not the surface topic but the real core thesis."
                ),
            },
            "hook": {
                "type": "string",
                "description": (
                    "The single most attention-grabbing line or idea from this specific video. "
                    "Should make someone stop scrolling. Max 220 characters."
                ),
            },
            "key_ideas": {
                "type": "array",
                "description": "3-8 distinct ideas from this video, ranked by shareability and impact.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short title for this idea (max 120 characters).",
                        },
                        "summary": {
                            "type": "string",
                            "description": "1-2 sentence explanation of the idea.",
                        },
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "1-2 direct quotes or close paraphrases from the transcript "
                                "that support this idea."
                            ),
                        },
                    },
                    "required": ["title", "summary", "evidence"],
                },
            },
            "quotes": {
                "type": "array",
                "description": (
                    "3-6 standalone powerful lines from the transcript that work as tweets "
                    "or pull-quotes on their own without any surrounding context."
                ),
                "items": {"type": "string"},
            },
            "data_points": {
                "type": "array",
                "description": (
                    "Any numbers, statistics, percentages, or research findings cited in the video. "
                    "Empty list if the video has none."
                ),
                "items": {"type": "string"},
            },
            "emotional_beats": {
                "type": "array",
                "description": (
                    "The emotional journey of this video — 3-5 moments that describe how "
                    "the viewer's feeling shifts as the video progresses. "
                    "E.g. 'Creator admits a past failure', 'Surprising realization lands', "
                    "'Practical breakthrough moment'."
                ),
                "items": {"type": "string"},
            },
            "story_structure": {
                "type": "array",
                "description": "3-4 narrative beats describing the structure of this specific video.",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "Beat label (e.g. Hook, Tension, Insight, Payoff, Reveal).",
                        },
                        "description": {
                            "type": "string",
                            "description": "What actually happens at this beat in the video.",
                        },
                    },
                    "required": ["label", "description"],
                },
            },
            "audience_takeaway": {
                "type": "string",
                "description": (
                    "The single most practical or memorable thing the audience takes away "
                    "from this video. One punchy sentence."
                ),
            },
        },
        "required": [
            "summary",
            "hook",
            "key_ideas",
            "quotes",
            "data_points",
            "emotional_beats",
            "story_structure",
            "audience_takeaway",
        ],
    },
}

_SYSTEM_PROMPT = """\
You are a content strategist who has studied viral content across every platform.
You think in terms of narrative structure, emotional hooks, and platform-native formats.

Your job is to deeply analyze YouTube video transcripts and extract the raw material
that makes content shareable. You don't summarize — you deconstruct.

When analyzing, ask yourself:
- What is the REAL core thesis (not just the surface topic)?
- Which exact lines would make someone stop scrolling on Twitter or LinkedIn?
- What emotional journey does the viewer go on?
- What would a creator's audience screenshot, quote, or save?
- What is the single most actionable or memorable takeaway?

Be ruthlessly specific to THIS video. Generic observations like "the creator discusses
important topics" or "this video covers useful information" are worthless outputs.
Every field you return must only make sense for this specific video and no other.\
"""


def analyze_content(transcript: Transcript, *, title: str | None = None) -> ContentAnalysis:
    settings = get_settings()

    if settings.anthropic_api_key:
        return _analyze_with_claude(transcript, title=title, api_key=settings.anthropic_api_key)

    if settings.groq_api_key:
        return _analyze_with_groq(transcript, title=title, api_key=settings.groq_api_key)

    if settings.google_api_key:
        return _analyze_with_gemini(transcript, title=title, api_key=settings.google_api_key)

    return _analyze_deterministic(transcript, title=title)


# ---------------------------------------------------------------------------
# Real Claude implementation
# ---------------------------------------------------------------------------


def _analyze_with_claude(
    transcript: Transcript,
    *,
    title: str | None,
    api_key: str,
) -> ContentAnalysis:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    video_context = f"Video title: {title}\n\n" if title else ""
    user_message = f"{video_context}Transcript:\n\n{transcript.text}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        tools=[_ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "content_analysis"},
        messages=[{"role": "user", "content": user_message}],
    )

    tool_block = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if tool_block is None:
        raise RuntimeError(
            "Claude did not return a structured analysis block. "
            "Check your ANTHROPIC_API_KEY and that the model is accessible."
        )

    data: dict[str, Any] = tool_block.input

    return ContentAnalysis(
        video_id=transcript.video_id,
        title=title,
        summary=data["summary"],
        hook=data["hook"][:220],
        key_ideas=[
            ContentIdea(
                title=idea["title"][:120],
                summary=idea["summary"],
                evidence=idea.get("evidence", []),
            )
            for idea in data["key_ideas"]
        ],
        quotes=data.get("quotes", []),
        data_points=data.get("data_points", []),
        emotional_beats=data.get("emotional_beats", []),
        story_structure=[
            StoryBeat(
                label=beat["label"][:80],
                description=beat["description"],
            )
            for beat in data["story_structure"]
        ],
        audience_takeaway=data["audience_takeaway"],
    )


# ---------------------------------------------------------------------------
# Groq implementation (free tier, 14K req/day — best free option)
# Model: llama-3.3-70b-versatile — strong reasoning, good JSON discipline
# ---------------------------------------------------------------------------


def _analyze_with_groq(
    transcript: Transcript,
    *,
    title: str | None,
    api_key: str,
) -> ContentAnalysis:
    import json

    from groq import Groq

    client = Groq(api_key=api_key)

    video_context = f"Video title: {title}\n\n" if title else ""
    user_message = (
        f"{video_context}Transcript:\n\n{transcript.text}\n\n"
        f"Return your analysis as a JSON object with these exact fields:\n{_GEMINI_JSON_SCHEMA}"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    data: dict[str, Any] = json.loads(response.choices[0].message.content)

    return ContentAnalysis(
        video_id=transcript.video_id,
        title=title,
        summary=data["summary"],
        hook=data["hook"][:220],
        key_ideas=[
            ContentIdea(
                title=idea["title"][:120],
                summary=idea["summary"],
                evidence=idea.get("evidence", []),
            )
            for idea in data["key_ideas"]
        ],
        quotes=data.get("quotes", []),
        data_points=data.get("data_points", []),
        emotional_beats=data.get("emotional_beats", []),
        story_structure=[
            StoryBeat(
                label=beat["label"][:80],
                description=beat["description"],
            )
            for beat in data["story_structure"]
        ],
        audience_takeaway=data["audience_takeaway"],
    )


# ---------------------------------------------------------------------------
# Gemini implementation (free tier — use when ANTHROPIC_API_KEY is not set)
# ---------------------------------------------------------------------------

_GEMINI_JSON_SCHEMA = """\
Return a JSON object with EXACTLY these fields:
{
  "summary": "2-3 sentences on the real core thesis of this video",
  "hook": "The single most attention-grabbing line from this video (max 220 chars)",
  "key_ideas": [
    {
      "title": "Short idea title (max 120 chars)",
      "summary": "1-2 sentence explanation specific to this video",
      "evidence": ["direct quote or close paraphrase from the transcript"]
    }
  ],
  "quotes": ["standalone line that works as a tweet on its own"],
  "data_points": ["any statistic, number, or research finding mentioned"],
  "emotional_beats": ["one emotional moment or shift in the video"],
  "story_structure": [
    {"label": "Hook", "description": "what happens at this beat"}
  ],
  "audience_takeaway": "single most memorable or actionable thing someone takes away"
}
Produce 3-8 key_ideas, 3-6 quotes, 3-5 emotional_beats, 3-4 story_structure beats.
data_points may be an empty list if the video has none.\
"""


def _analyze_with_gemini(
    transcript: Transcript,
    *,
    title: str | None,
    api_key: str,
) -> ContentAnalysis:
    import json

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    video_context = f"Video title: {title}\n\n" if title else ""
    user_message = (
        f"{video_context}Transcript:\n\n{transcript.text}\n\n{_GEMINI_JSON_SCHEMA}"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )

    data: dict[str, Any] = json.loads(response.text)

    return ContentAnalysis(
        video_id=transcript.video_id,
        title=title,
        summary=data["summary"],
        hook=data["hook"][:220],
        key_ideas=[
            ContentIdea(
                title=idea["title"][:120],
                summary=idea["summary"],
                evidence=idea.get("evidence", []),
            )
            for idea in data["key_ideas"]
        ],
        quotes=data.get("quotes", []),
        data_points=data.get("data_points", []),
        emotional_beats=data.get("emotional_beats", []),
        story_structure=[
            StoryBeat(
                label=beat["label"][:80],
                description=beat["description"],
            )
            for beat in data["story_structure"]
        ],
        audience_takeaway=data["audience_takeaway"],
    )


# ---------------------------------------------------------------------------
# Deterministic fallback — used when ANTHROPIC_API_KEY is not set.
# Keeps tests green and lets the rest of the pipeline run without a key.
# ---------------------------------------------------------------------------


def _analyze_deterministic(
    transcript: Transcript,
    *,
    title: str | None = None,
) -> ContentAnalysis:
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
    return " ".join(sentences[:3])[:700]


def _extract_ideas(sentences: list[str]) -> list[ContentIdea]:
    substantial = [s for s in sentences if len(s.split()) >= 8]
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
    return [s for s in sentences if len(s.split()) <= 18][:3]


def _extract_data_points(sentences: list[str]) -> list[str]:
    return [s for s in sentences if re.search(r"\d", s)][:5]


def _extract_emotional_beats(sentences: list[str]) -> list[str]:
    markers = ("struggle", "mistake", "surprise", "fear", "hope", "win", "failed", "learned")
    beats = [s for s in sentences if any(m in s.lower() for m in markers)]
    return beats[:5] or ["The transcript introduces a problem, develops tension, and resolves it."]


def _audience_takeaway(ideas: list[ContentIdea]) -> str:
    return f"Use the core insight from '{ideas[0].title}' as the practical takeaway."
