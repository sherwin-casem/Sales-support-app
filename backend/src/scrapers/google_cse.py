"""Google Custom Search JSON API — discover company URLs from web search."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from src.common.config import Settings, get_settings
from src.scrapers.website import GENERIC_DOMAINS

CSE_API_URL = "https://www.googleapis.com/customsearch/v1"


@dataclass
class WebSearchResult:
    url: str
    title: str
    snippet: str


def _domain_from_url(url: str) -> str:
    netloc = urlparse(url).netloc.lower().removeprefix("www.")
    return netloc


def ensure_cse_configured(settings: Settings | None = None) -> Settings:
    settings = settings or get_settings()
    if not settings.google_cse_api_key or not settings.google_cse_cx:
        raise ValueError(
            "Google Custom Search is not configured. Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX."
        )
    if not settings.google_cse_api_key.startswith("AIza"):
        raise ValueError(
            "GOOGLE_CSE_API_KEY looks invalid (expected a Google Cloud API key starting with 'AIza'). "
            "Create one at Google Cloud Console → APIs & Services → Credentials, with Custom Search API enabled."
        )
    return settings


def search_google(
    query: str,
    *,
    num: int = 10,
    start: int = 1,
    settings: Settings | None = None,
) -> list[WebSearchResult]:
    """Execute a single Google CSE request (num max 10, start is 1-based)."""
    settings = ensure_cse_configured(settings)
    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_cx,
        "q": query,
        "num": min(max(num, 1), 10),
        "start": max(start, 1),
    }

    with httpx.Client(timeout=settings.scraper_timeout_seconds) as client:
        response = client.get(CSE_API_URL, params=params)
        if response.status_code >= 400:
            detail = response.text[:500]
            if response.status_code == 401:
                raise ValueError(
                    "Google Custom Search rejected the API key (401 Unauthorized). "
                    "Use a Google Cloud API key starting with 'AIza' from a project with "
                    "Custom Search API enabled — not an OAuth or access token."
                )
            if response.status_code == 403:
                raise ValueError(
                    "Google Custom Search denied access (403). Enable Custom Search API "
                    f"in Google Cloud Console and verify billing/quota. Response: {detail}"
                )
            raise ValueError(
                f"Google Custom Search request failed ({response.status_code}): {detail}"
            )
        data = response.json()

    results: list[WebSearchResult] = []
    for item in data.get("items") or []:
        link = item.get("link")
        if not link:
            continue
        results.append(
            WebSearchResult(
                url=link,
                title=item.get("title") or "",
                snippet=item.get("snippet") or "",
            )
        )
    return results


def discover_company_urls(
    queries: list[str],
    max_results: int,
    settings: Settings | None = None,
) -> list[WebSearchResult]:
    """Run one or more search queries and return deduplicated results by domain."""
    settings = ensure_cse_configured(settings)
    seen_domains: set[str] = set()
    collected: list[WebSearchResult] = []

    for query in queries:
        if len(collected) >= max_results:
            break
        start = 1
        while len(collected) < max_results:
            batch_size = min(10, max_results - len(collected))
            batch = search_google(query, num=batch_size, start=start, settings=settings)
            if not batch:
                break
            for result in batch:
                domain = _domain_from_url(result.url)
                if not domain or domain in GENERIC_DOMAINS or domain in seen_domains:
                    continue
                seen_domains.add(domain)
                collected.append(result)
                if len(collected) >= max_results:
                    break
            if len(batch) < batch_size:
                break
            start += 10

    return collected
