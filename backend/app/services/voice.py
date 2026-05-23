from __future__ import annotations

import re

from app.schemas.voice import VoiceStyle


def extract_voice_style(samples: list[str]) -> VoiceStyle:
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", " ".join(samples).lower())
    sentence_count = max(1, len(re.findall(r"[.!?]", " ".join(samples))))
    avg_sentence_length = len(words) / sentence_count
    vocabulary = _signature_words(words)
    emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF]", " ".join(samples)))

    if avg_sentence_length < 12:
        sentence_length = "short and punchy"
    elif avg_sentence_length > 24:
        sentence_length = "long-form and explanatory"
    else:
        sentence_length = "balanced"

    return VoiceStyle(
        tone=_infer_tone(" ".join(samples)),
        vocabulary=vocabulary,
        sentence_length=sentence_length,
        emoji_usage="frequent" if emoji_count >= len(samples) else "minimal",
        sample_count=len(samples),
    )


def _signature_words(words: list[str]) -> list[str]:
    stop_words = {
        "the",
        "and",
        "you",
        "that",
        "this",
        "with",
        "for",
        "from",
        "into",
        "your",
        "are",
        "but",
    }
    counts: dict[str, int] = {}
    for word in words:
        if len(word) < 5 or word in stop_words:
            continue
        counts[word] = counts.get(word, 0) + 1
    return [
        word
        for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    ]


def _infer_tone(text: str) -> str:
    lower = text.lower()
    if any(marker in lower for marker in ("mistake", "wrong", "stop", "hard truth")):
        return "direct and contrarian"
    if any(marker in lower for marker in ("here's how", "step", "framework", "system")):
        return "practical and instructional"
    if any(marker in lower for marker in ("story", "learned", "felt", "realized")):
        return "reflective and narrative"
    return "clear and pragmatic"

