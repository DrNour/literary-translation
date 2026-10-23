"""Lightweight, transparent analytics used by the teaching dashboard.

The sentiment and emotion routines are deliberately labelled exploratory. They
are useful for classroom comparison and hypothesis generation, not as a
replacement for validated linguistic annotation.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

import pandas as pd


TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_'’]+|[\u0600-\u06ff]+")


POSITIVE = {
    "good",
    "best",
    "lovely",
    "hope",
    "happy",
    "beauty",
    "love",
    "joy",
    "kind",
    "light",
    "success",
    "خير",
    "جميل",
    "جمال",
    "حب",
    "فرح",
    "سعيد",
    "أمل",
    "نور",
    "كرم",
}

NEGATIVE = {
    "worst",
    "darkness",
    "despair",
    "death",
    "grief",
    "weak",
    "tired",
    "sad",
    "war",
    "loss",
    "bad",
    "حزن",
    "موت",
    "ظلام",
    "يأس",
    "ضعف",
    "تعب",
    "فقد",
    "حرب",
}

EMOTION_LEXICON = {
    "joy": {"joy", "happy", "happiness", "laugh", "فرح", "سعيد", "سعادة"},
    "love": {"love", "lovely", "beauty", "heart", "حب", "حبيب", "جمال"},
    "sadness": {"sad", "grief", "death", "despair", "mourning", "حزن", "موت", "يأس", "رثاء"},
    "fear": {"fear", "darkness", "terror", "afraid", "خوف", "رعب", "ظلام"},
    "anger": {"anger", "war", "rage", "غضب", "حرب", "سيف"},
    "hope": {"hope", "light", "future", "أمل", "نور", "مستقبل"},
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text or "")]


def word_count(text: str) -> int:
    return len(tokenize(text))


def diff_metrics(original: str, revised: str) -> dict[str, Any]:
    """Return interpretable token-level edit statistics."""

    before = (original or "").split()
    after = (revised or "").split()
    matcher = SequenceMatcher(a=before, b=after)
    added = 0
    removed = 0
    replacements = 0
    unchanged = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            unchanged += i2 - i1
        elif tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "replace":
            removed += i2 - i1
            added += j2 - j1
            replacements += 1
    denominator = max(len(before), 1)
    return {
        "source_tokens": len(before),
        "revised_tokens": len(after),
        "added_tokens": added,
        "removed_tokens": removed,
        "replacement_blocks": replacements,
        "unchanged_tokens": unchanged,
        "edit_rate": round((added + removed) / denominator, 3),
        "similarity": round(matcher.ratio(), 3),
    }


def elapsed_minutes(started_at: str | None, ended_at: str | None) -> float | None:
    if not started_at or not ended_at:
        return None
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
        return round(max((end - start).total_seconds() / 60, 0), 2)
    except (TypeError, ValueError):
        return None


def sentiment_profile(text: str) -> dict[str, Any]:
    tokens = tokenize(text)
    positive = sum(token in POSITIVE for token in tokens)
    negative = sum(token in NEGATIVE for token in tokens)
    emotions = Counter(
        emotion
        for token in tokens
        for emotion, vocabulary in EMOTION_LEXICON.items()
        if token in vocabulary
    )
    dominant = emotions.most_common(1)[0][0] if emotions else "none detected"
    polarity = (positive - negative) / max(len(tokens), 1)
    return {
        "words": len(tokens),
        "positive_hits": positive,
        "negative_hits": negative,
        "polarity": round(polarity, 3),
        "dominant_emotion": dominant,
        "emotion_counts": dict(emotions),
    }


def sentiment_table(texts: dict[str, str]) -> pd.DataFrame:
    rows = []
    for label, text in texts.items():
        profile = sentiment_profile(text)
        rows.append(
            {
                "version": label,
                "words": profile["words"],
                "polarity": profile["polarity"],
                "dominant emotion": profile["dominant_emotion"],
                "positive hits": profile["positive_hits"],
                "negative hits": profile["negative_hits"],
            }
        )
    return pd.DataFrame(rows)


def teacher_average(review: dict[str, Any]) -> float:
    keys = ["fidelity_score", "style_score", "cultural_score", "creativity_score"]
    values = [float(review.get(key, 0)) for key in keys]
    return round(sum(values) / len(values), 2) if values else 0.0


def icc_two_way_random(ratings: list[dict[str, Any]]) -> float | None:
    """Calculate a two-way random-effects single-measure ICC(2,1).

    The function expects one row per item/rater pair with keys ``item``,
    ``rater`` and ``score``. It returns ``None`` when the data are not suitable
    for an ICC calculation.
    """

    if not ratings:
        return None
    frame = pd.DataFrame(ratings)
    if not {"item", "rater", "score"}.issubset(frame.columns):
        return None
    table = frame.pivot_table(index="item", columns="rater", values="score", aggfunc="mean").dropna()
    n, k = table.shape
    if n < 2 or k < 2:
        return None
    values = table.to_numpy(dtype=float)
    grand = values.mean()
    row_means = values.mean(axis=1)
    col_means = values.mean(axis=0)
    msr = k * ((row_means - grand) ** 2).sum() / (n - 1)
    msc = n * ((col_means - grand) ** 2).sum() / (k - 1)
    residuals = values - row_means[:, None] - col_means[None, :] + grand
    mse = (residuals**2).sum() / ((n - 1) * (k - 1))
    denominator = msr + (k - 1) * mse + k * (msc - mse) / n
    if denominator == 0:
        return None
    return round(float((msr - mse) / denominator), 3)

