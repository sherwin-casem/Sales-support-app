"""Tests for URL utilities."""

from src.common.url_utils import normalize_domain, normalize_website


def test_normalize_domain():
    assert normalize_domain("https://www.Example.com/about") == "example.com"
    assert normalize_domain("example.com") == "example.com"


def test_normalize_website():
    assert normalize_website("example.com") == "https://example.com"
