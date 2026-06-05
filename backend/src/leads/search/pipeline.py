"""Lead search pipeline — web search, scrape, light enrich, score."""

from __future__ import annotations

from urllib.parse import urlparse

from src.ai.openai_client import (
    build_web_search_queries,
    infer_industry_from_text,
    parse_lead_search_query,
    score_leads_against_criteria,
)
from src.common.config import get_settings
from src.common.url_utils import normalize_domain, normalize_website
from src.leads.dedup import find_duplicate_sync
from src.leads.search.schemas import LeadPreviewItem, LeadSearchCriteria
from src.scrapers.google_cse import WebSearchResult, discover_company_urls, ensure_cse_configured
from src.scrapers.website import crawl_seed_urls, fetch_page

DIRECTORY_HINTS = (
    "directory",
    "members",
    "member-list",
    "companies",
    "company-list",
    "listings",
    "suppliers",
    "associations",
    "exhibitors",
)


def _is_directory_page(url: str, title: str) -> bool:
    combined = f"{url} {title}".lower()
    return any(hint in combined for hint in DIRECTORY_HINTS)


def _company_name_from_result(result: WebSearchResult, page_title: str | None = None) -> str:
    title = (page_title or result.title or "").strip()
    if title:
        for sep in ("|", "–", "-", ":", " — "):
            if sep in title:
                title = title.split(sep)[0].strip()
        if title and len(title) >= 2:
            return title[:255]

    domain = urlparse(result.url).netloc.lower().removeprefix("www.")
    name_part = domain.split(".")[0]
    return name_part.replace("-", " ").title()[:255]


def _enrich_candidate(
    *,
    company_name: str,
    website: str | None,
    email: str | None,
    phone: str | None,
    country: str | None,
    industry: str | None,
    scraped_title: str | None,
    session,
    default_country: str | None,
    default_industry: str | None,
) -> dict:
    if website:
        page = fetch_page(normalize_website(website) or website)
        if page:
            scraped_title = page.title or scraped_title
            if page.emails and not email:
                email = page.emails[0]
            if page.phones and not phone:
                phone = page.phones[0]
            inferred = infer_industry_from_text(page.text[:3000])
            if inferred:
                industry = inferred

    country = country or default_country
    industry = industry or default_industry

    duplicate = find_duplicate_sync(
        session,
        company_name=company_name,
        website=website,
        email=email,
    )

    return {
        "company_name": company_name,
        "website": normalize_website(website),
        "email": email,
        "phone": phone,
        "country": country,
        "industry": industry,
        "scraped_title": scraped_title,
        "already_in_pipeline": duplicate is not None,
    }


def _extract_from_directory(
    result: WebSearchResult,
    *,
    max_pages: int,
    industries: list[str],
    countries: list[str],
    session,
    seen_domains: set[str],
    default_country: str | None,
    default_industry: str | None,
) -> tuple[list[dict], int]:
    extracted, pages = crawl_seed_urls(
        [result.url],
        max_pages=min(5, max_pages),
        crawl_depth=1,
        industries=industries,
        countries=countries,
    )
    candidates: list[dict] = []
    for item in extracted:
        domain = normalize_domain(item.website)
        if domain and domain in seen_domains:
            continue
        if domain:
            seen_domains.add(domain)
        candidates.append(
            _enrich_candidate(
                company_name=item.company_name,
                website=item.website,
                email=item.email,
                phone=item.phone,
                country=item.country,
                industry=default_industry,
                scraped_title=None,
                session=session,
                default_country=default_country,
                default_industry=default_industry,
            )
        )
    return candidates, pages


def _extract_from_company_page(
    result: WebSearchResult,
    *,
    session,
    seen_domains: set[str],
    default_country: str | None,
    default_industry: str | None,
) -> tuple[list[dict], int]:
    domain = normalize_domain(result.url)
    if domain and domain in seen_domains:
        return [], 0
    if domain:
        seen_domains.add(domain)

    page = fetch_page(result.url)
    pages = 1 if page else 0
    website = normalize_website(result.url)
    company_name = _company_name_from_result(result, page.title if page else None)

    email = page.emails[0] if page and page.emails else None
    phone = page.phones[0] if page and page.phones else None
    industry = default_industry
    scraped_title = page.title if page else result.title

    if page:
        inferred = infer_industry_from_text(page.text[:3000])
        if inferred:
            industry = inferred

    candidate = _enrich_candidate(
        company_name=company_name,
        website=website,
        email=email,
        phone=phone,
        country=default_country,
        industry=industry,
        scraped_title=scraped_title,
        session=session,
        default_country=default_country,
        default_industry=default_industry,
    )
    return [candidate], pages


def run_search_pipeline(
    query: str,
    max_results: int,
    session,
) -> tuple[LeadSearchCriteria, list[LeadPreviewItem], int, list[str]]:
    settings = ensure_cse_configured(get_settings())

    criteria_dict = parse_lead_search_query(query)
    criteria = LeadSearchCriteria.model_validate(criteria_dict)

    search_queries = build_web_search_queries(criteria_dict, query)
    cap = min(max_results, settings.google_cse_max_results)
    discovered = discover_company_urls(search_queries, max_results=cap, settings=settings)
    discovered_urls = [r.url for r in discovered]

    if not discovered:
        raise ValueError("No companies found from web search. Try a different query.")

    default_country = criteria.countries[0] if criteria.countries else None
    default_industry = criteria.industries[0] if criteria.industries else None

    candidates: list[dict] = []
    seen_domains: set[str] = set()
    pages_crawled = 0
    page_budget = max_results * 2

    for result in discovered:
        if pages_crawled >= page_budget:
            break

        if _is_directory_page(result.url, result.title):
            batch, pages = _extract_from_directory(
                result,
                max_pages=page_budget - pages_crawled,
                industries=criteria.industries,
                countries=criteria.countries,
                session=session,
                seen_domains=seen_domains,
                default_country=default_country,
                default_industry=default_industry,
            )
        else:
            batch, pages = _extract_from_company_page(
                result,
                session=session,
                seen_domains=seen_domains,
                default_country=default_country,
                default_industry=default_industry,
            )

        candidates.extend(batch)
        pages_crawled += pages

    if not candidates:
        raise ValueError("Web search returned URLs but no company data could be extracted.")

    scored = score_leads_against_criteria(candidates, criteria_dict)

    preview_items = [
        LeadPreviewItem(
            company_name=c["company_name"],
            website=c.get("website"),
            email=c.get("email"),
            phone=c.get("phone"),
            country=c.get("country"),
            industry=c.get("industry"),
            match_score=c["match_score"],
            match_reason=c.get("match_reason", ""),
            scraped_title=c.get("scraped_title"),
            already_in_pipeline=c.get("already_in_pipeline", False),
        )
        for c in scored
    ]

    return criteria, preview_items, pages_crawled, discovered_urls
