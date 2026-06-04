"""Intent signal detection from page content."""

from __future__ import annotations

from dataclasses import dataclass

from src.common.enums import IntentSignalType

HIRING_KEYWORDS = ("hiring", "careers", "job opening", "we're hiring", "join our team", "vacancy")
EXPANSION_KEYWORDS = ("expansion", "new facility", "opening office", "growing", "new plant", "acquisition")
FUNDING_KEYWORDS = ("funding", "investment", "series a", "series b", "raised", "venture capital", "ipo")


@dataclass
class DetectedIntent:
    signal_type: IntentSignalType
    evidence: str
    score: int


def detect_intent_signals(text: str) -> list[DetectedIntent]:
    lower = text.lower()
    signals: list[DetectedIntent] = []

    for kw in HIRING_KEYWORDS:
        if kw in lower:
            idx = lower.index(kw)
            snippet = text[max(0, idx - 40) : idx + len(kw) + 60].strip()
            signals.append(DetectedIntent(IntentSignalType.HIRING, snippet[:500], 3))
            break

    for kw in EXPANSION_KEYWORDS:
        if kw in lower:
            idx = lower.index(kw)
            snippet = text[max(0, idx - 40) : idx + len(kw) + 60].strip()
            signals.append(DetectedIntent(IntentSignalType.EXPANSION, snippet[:500], 2))
            break

    for kw in FUNDING_KEYWORDS:
        if kw in lower:
            idx = lower.index(kw)
            snippet = text[max(0, idx - 40) : idx + len(kw) + 60].strip()
            signals.append(DetectedIntent(IntentSignalType.FUNDING, snippet[:500], 4))
            break

    return signals


def total_intent_score(signals: list[DetectedIntent]) -> int:
    return sum(s.score for s in signals)
