"""Tests for intent detection."""

from src.intent.detector import detect_intent_signals, total_intent_score
from src.common.enums import IntentSignalType


def test_detect_hiring_signal():
    text = "We are hiring engineers for our new automation team. Join our team today."
    signals = detect_intent_signals(text)
    assert any(s.signal_type == IntentSignalType.HIRING for s in signals)
    assert total_intent_score(signals) >= 3


def test_detect_no_signal():
    assert detect_intent_signals("Welcome to our homepage.") == []
