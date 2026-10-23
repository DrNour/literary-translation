"""Optional AI assistance with a transparent, offline demo fallback."""

from __future__ import annotations

import os
from typing import Any


MODE_INSTRUCTIONS = {
    "Meaning-focused": (
        "Preserve the propositional meaning, relationships, tense, and pragmatic force. "
        "Use natural target-language phrasing without flattening important ambiguity."
    ),
    "Style-focused": (
        "Preserve the author's voice, register, rhythm, imagery, repetition, and narrative distance. "
        "Explain any unavoidable stylistic trade-offs briefly."
    ),
    "Creative alternative": (
        "Offer an inventive literary alternative that remains defensible as a translation. "
        "Prioritise literary effect while identifying any deliberate departures from literal wording."
    ),
}


def configured_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def api_is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _openai_suggestion(source_text: str, draft: str, direction: str, mode: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    system = (
        "You are a literary-translation workshop assistant. The student must remain the decision-maker. "
        "Return one complete translation only, followed by a short paragraph identifying the main trade-offs. "
        "Do not invent source content. Work in the requested language direction."
    )
    user = f"""Language direction: {direction}
Workshop mode: {mode}
Instruction: {MODE_INSTRUCTIONS[mode]}

SOURCE TEXT:
{source_text}

STUDENT'S UNAIDED DRAFT:
{draft}
"""
    model = configured_model()
    if hasattr(client, "responses"):
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            store=False,
        )
        output = getattr(response, "output_text", None)
        if output:
            return output.strip()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _demo_suggestion(draft: str, mode: str) -> str:
    """Keep the workflow usable without an API key; never present this as AI output."""

    return (
        "[Offline demo scaffold — configure OPENAI_API_KEY for a generated alternative]\n\n"
        f"{mode} revision target:\n{draft.strip()}\n\n"
        f"Workshop prompt: {MODE_INSTRUCTIONS[mode]}"
    )


def generate_suggestions(source_text: str, draft: str, direction: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for mode in MODE_INSTRUCTIONS:
        if api_is_configured():
            try:
                suggestion = _openai_suggestion(source_text, draft, direction, mode)
                provider = "OpenAI (store=False)"
                model = configured_model()
            except Exception as exc:  # pragma: no cover - depends on external credentials/network
                suggestion = _demo_suggestion(draft, mode)
                provider = f"Offline fallback after API error: {type(exc).__name__}"
                model = "offline-demo"
        else:
            suggestion = _demo_suggestion(draft, mode)
            provider = "Offline demo"
            model = "offline-demo"
        results.append({"mode": mode, "suggestion": suggestion, "model": model, "provider": provider})
    return results

