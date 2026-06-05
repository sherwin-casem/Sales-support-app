"""Tests for lead search — web search discovery, query building, save flow."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.openai_client import _fallback_score_leads, _fallback_web_search_queries
from src.common.enums import CrawlRunStatus, LeadSource
from src.leads.models import Lead
from src.leads.search.models import LeadSearchRun
from src.leads.search.schemas import LeadSearchSaveItem, LeadSearchSaveRequest
from src.leads.search.service import LeadSearchService
from src.scrapers.google_cse import discover_company_urls, ensure_cse_configured
from src.scrapers.website import PageData
from src.users.models import User

FIXTURES = Path(__file__).parent / "fixtures"
CSE_FIXTURE = json.loads((FIXTURES / "google_cse_response.json").read_text(encoding="utf-8"))


def test_fallback_web_search_queries_builds_from_criteria():
    criteria = {
        "keywords": ["water", "treatment"],
        "industries": ["utilities"],
        "countries": ["India"],
    }
    queries = _fallback_web_search_queries(criteria, "water treatment plants in India")
    assert len(queries) == 1
    assert "companies" in queries[0]
    assert "water" in queries[0]


def test_fallback_score_leads_filters_by_keywords():
    candidates = [
        {"company_name": "Acme Water Treatment", "industry": None, "country": None, "website": "", "scraped_title": ""},
        {"company_name": "Random Corp", "industry": None, "country": None, "website": "", "scraped_title": ""},
    ]
    criteria = {"keywords": ["water", "treatment"], "industries": [], "countries": []}
    scored = _fallback_score_leads(candidates, criteria, threshold=40)
    assert len(scored) >= 1
    assert scored[0]["company_name"] == "Acme Water Treatment"


def test_ensure_cse_configured_raises_without_keys():
    from src.common.config import Settings

    settings = Settings(google_cse_api_key="", google_cse_cx="")
    with pytest.raises(ValueError, match="Google Custom Search is not configured"):
        ensure_cse_configured(settings)


def test_ensure_cse_configured_rejects_invalid_key_format():
    from src.common.config import Settings

    settings = Settings(google_cse_api_key="AQ.not-a-real-key", google_cse_cx="cx123")
    with pytest.raises(ValueError, match="AIza"):
        ensure_cse_configured(settings)


def test_discover_company_urls_deduplicates_domains():
    from src.common.config import Settings

    settings = Settings(google_cse_api_key="AIzaSyTestKey123", google_cse_cx="test-cx")

    with patch("src.scrapers.google_cse.search_google") as mock_search:
        mock_search.return_value = [
            type("R", (), {"url": "https://acme-water.example/", "title": "Acme", "snippet": ""})(),
            type("R", (), {"url": "https://www.acme-water.example/about", "title": "About", "snippet": ""})(),
            type("R", (), {"url": "https://process-auto.example/", "title": "Process Auto", "snippet": ""})(),
        ]
        results = discover_company_urls(["water treatment India"], max_results=10, settings=settings)

    assert len(results) == 2
    domains = {r.url.split("//")[1].split("/")[0].removeprefix("www.") for r in results}
    assert "acme-water.example" in domains
    assert "process-auto.example" in domains


def test_discover_company_urls_calls_google_api():
    from src.common.config import Settings

    settings = Settings(google_cse_api_key="AIzaSyTestKey123", google_cse_cx="test-cx")

    with patch("src.scrapers.google_cse.httpx.Client") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = CSE_FIXTURE
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        results = discover_company_urls(["water treatment India"], max_results=5, settings=settings)

    assert len(results) == 3
    assert results[0].url.startswith("https://")


@pytest.mark.asyncio
async def test_save_preview_leads_creates_search_source_leads(db_session: AsyncSession) -> None:
    user = User(
        id=uuid.uuid4(),
        email=f"search-{uuid.uuid4()}@example.com",
        password_hash="hashed",
        full_name="Search Tester",
    )
    db_session.add(user)
    await db_session.flush()

    run = LeadSearchRun(
        created_by=user.id,
        query_text="water treatment in India",
        seed_urls=["https://acme-water.example/"],
        status=CrawlRunStatus.COMPLETED,
        preview_results=[],
    )
    db_session.add(run)
    await db_session.flush()

    payload = LeadSearchSaveRequest(
        items=[
            LeadSearchSaveItem(
                company_name="Acme Water",
                website="https://acme-water.example",
                email="info@acme-water.example",
                country="IN",
                industry="Water treatment",
            )
        ]
    )

    with patch("src.jobs.tasks.enrich_lead_task.delay", MagicMock()) as mock_enrich:
        response = await LeadSearchService(db_session).save_preview_leads(user, run.id, payload)

    assert response.created == 1
    assert response.skipped == 0
    assert len(response.lead_ids) == 1
    mock_enrich.assert_called_once()

    lead = await db_session.scalar(select(Lead).where(Lead.id == response.lead_ids[0]))
    assert lead is not None
    assert lead.source == LeadSource.SEARCH
    assert lead.company_name == "Acme Water"


def test_run_search_pipeline_with_mocked_cse():
    from src.leads.search.pipeline import run_search_pipeline

    mock_results = [
        type("R", (), {
            "url": "https://acme-water.example/",
            "title": "Acme Water Treatment",
            "snippet": "Water treatment in India",
        })(),
    ]
    mock_page = PageData(
        url="https://acme-water.example/",
        title="Acme Water Treatment",
        text="Water treatment and process automation in India",
        emails=["info@acme-water.example"],
        phones=["+91 1234567890"],
    )

    from src.common.config import Settings

    settings = Settings(google_cse_api_key="test", google_cse_cx="test", google_cse_max_results=20)

    with (
        patch("src.leads.search.pipeline.ensure_cse_configured", return_value=settings),
        patch("src.leads.search.pipeline.get_settings", return_value=settings),
        patch("src.leads.search.pipeline.parse_lead_search_query") as mock_parse,
        patch("src.leads.search.pipeline.build_web_search_queries") as mock_queries,
        patch("src.leads.search.pipeline.discover_company_urls") as mock_discover,
        patch("src.leads.search.pipeline.fetch_page") as mock_fetch,
        patch("src.leads.search.pipeline.infer_industry_from_text") as mock_industry,
        patch("src.leads.search.pipeline.score_leads_against_criteria") as mock_score,
        patch("src.leads.search.pipeline.find_duplicate_sync") as mock_dedup,
    ):
        mock_parse.return_value = {
            "industries": ["water treatment"],
            "countries": ["India"],
            "keywords": ["water", "automation"],
            "company_signals": [],
            "exclude_keywords": [],
            "relevance_notes": "",
        }
        mock_queries.return_value = ["water treatment India companies"]
        mock_discover.return_value = mock_results
        mock_fetch.return_value = mock_page
        mock_industry.return_value = "Water treatment"
        mock_dedup.return_value = None
        mock_score.return_value = [{
            "company_name": "Acme Water Treatment",
            "website": "https://acme-water.example/",
            "email": "info@acme-water.example",
            "phone": "+91 1234567890",
            "country": "India",
            "industry": "Water treatment",
            "match_score": 85,
            "match_reason": "Strong match",
            "scraped_title": "Acme Water Treatment",
            "already_in_pipeline": False,
        }]

        criteria, preview_items, pages, discovered_urls = run_search_pipeline(
            "water treatment plants in India",
            max_results=10,
            session=MagicMock(),
        )

    assert len(preview_items) == 1
    assert preview_items[0].company_name == "Acme Water Treatment"
    assert preview_items[0].match_score == 85
    assert discovered_urls == ["https://acme-water.example/"]
    assert pages >= 1
