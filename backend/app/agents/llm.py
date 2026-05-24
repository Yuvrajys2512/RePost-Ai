"""Shared LLM caller — picks the configured provider automatically.

Priority: Claude (Anthropic) → Groq → Gemini
All generators and nodes import from here instead of managing provider
selection themselves.
"""

from __future__ import annotations

import json
from typing import Any

from app.config import get_settings


def has_llm_provider() -> bool:
    s = get_settings()
    return bool(s.anthropic_api_key or s.groq_api_key or s.google_api_key)


def call_llm_json(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.6,
) -> dict[str, Any]:
    """Call the configured LLM and return the parsed JSON response.

    Raises RuntimeError if no provider key is configured.
    """
    settings = get_settings()

    if settings.anthropic_api_key:
        return _claude_json(system_prompt, user_message, settings.anthropic_api_key)
    if settings.groq_api_key:
        return _groq_json(system_prompt, user_message, settings.groq_api_key, temperature)
    if settings.google_api_key:
        return _gemini_json(system_prompt, user_message, settings.google_api_key)

    raise RuntimeError(
        "No AI provider key configured. Set ANTHROPIC_API_KEY, GROQ_API_KEY, or "
        "GOOGLE_API_KEY in backend/.env."
    )


def _claude_json(system: str, user_message: str, api_key: str) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system + "\n\nRespond with valid JSON only. No text before or after the JSON object.",
        messages=[{"role": "user", "content": user_message}],
    )
    return json.loads(response.content[0].text)


def _groq_json(
    system: str,
    user_message: str,
    api_key: str,
    temperature: float,
) -> dict[str, Any]:
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)


def _gemini_json(system: str, user_message: str, api_key: str) -> dict[str, Any]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)
