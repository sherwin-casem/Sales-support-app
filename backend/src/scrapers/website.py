"""Web scraping utilities — httpx + BeautifulSoup."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from src.common.config import get_settings

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")

GENERIC_DOMAINS = frozenset(
    {
        "facebook.com",
        "twitter.com",
        "linkedin.com",
        "instagram.com",
        "youtube.com",
        "google.com",
        "github.com",
        "wikipedia.org",
    }
)

LEADERSHIP_PATH_HINTS = ("about", "team", "leadership", "management", "people", "our-team", "company")
CAREERS_PATH_HINTS = ("careers", "jobs", "hiring", "join-us", "work-with-us")
NEWS_PATH_HINTS = ("news", "press", "media", "blog")


@dataclass
class ExtractedLead:
    company_name: str
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None


@dataclass
class PageData:
    url: str
    title: str | None = None
    description: str | None = None
    text: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)


@dataclass
class DecisionMakerCandidate:
    name: str
    role: str | None = None
    email: str | None = None
    linkedin: str | None = None


def _can_fetch(url: str, user_agent: str = "SalesIntelligenceBot/1.0") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
        return parser.can_fetch(user_agent, url)
    except Exception:
        return True


def fetch_page(url: str) -> PageData | None:
    settings = get_settings()
    if not _can_fetch(url):
        return None

    try:
        with httpx.Client(timeout=settings.scraper_timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "SalesIntelligenceBot/1.0"})
            if response.status_code >= 400:
                return None
            html = response.text
    except httpx.HTTPError:
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc.get("content", "").strip() if meta_desc else None

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ", strip=True).split())

    emails = list({m.group(0).lower() for m in EMAIL_PATTERN.finditer(html)})
    phones = list({m.group(0).strip() for m in PHONE_PATTERN.finditer(text)[:5]})

    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(url, href)
        links.append(absolute)

    return PageData(
        url=url,
        title=title,
        description=description,
        text=text[:50000],
        emails=emails,
        phones=phones,
        links=links,
    )


def _is_external_business_link(link: str, seed_domain: str) -> bool:
    domain = urlparse(link).netloc.lower().removeprefix("www.")
    if not domain or domain == seed_domain:
        return False
    return domain not in GENERIC_DOMAINS


def extract_leads_from_page(page: PageData, seed_domain: str, industries: list[str], countries: list[str]) -> list[ExtractedLead]:
    leads: list[ExtractedLead] = []
    seen_domains: set[str] = set()

    for link in page.links:
        domain = urlparse(link).netloc.lower().removeprefix("www.")
        if not _is_external_business_link(link, seed_domain) or domain in seen_domains:
            continue
        seen_domains.add(domain)

        company_name = domain.split(".")[0].replace("-", " ").title()
        if len(company_name) < 2:
            continue

        website = f"https://{domain}"
        country = countries[0] if countries else None
        industry = industries[0] if industries else None

        leads.append(
            ExtractedLead(
                company_name=company_name,
                website=website,
                email=page.emails[0] if page.emails else None,
                phone=page.phones[0] if page.phones else None,
                country=country,
            )
        )

    # Also extract from anchor text on seed page (directory listings)
    return leads


def crawl_seed_urls(
    seed_urls: list[str],
    max_pages: int,
    crawl_depth: int,
    industries: list[str],
    countries: list[str],
) -> tuple[list[ExtractedLead], int]:
    """BFS crawl from seeds; returns extracted leads and pages crawled."""
    all_leads: list[ExtractedLead] = []
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(url, 0) for url in seed_urls]
    pages_crawled = 0

    while queue and pages_crawled < max_pages:
        url, depth = queue.pop(0)
        normalized = url.rstrip("/")
        if normalized in visited:
            continue
        visited.add(normalized)

        page = fetch_page(url)
        if page is None:
            continue
        pages_crawled += 1

        seed_domain = urlparse(url).netloc.lower().removeprefix("www.")
        all_leads.extend(extract_leads_from_page(page, seed_domain, industries, countries))

        if depth < crawl_depth:
            for link in page.links:
                link_domain = urlparse(link).netloc.lower().removeprefix("www.")
                if link_domain == seed_domain and link.rstrip("/") not in visited:
                    queue.append((link, depth + 1))

    return all_leads, pages_crawled


def find_subpages(base_url: str, hints: tuple[str, ...]) -> list[str]:
    page = fetch_page(base_url)
    if page is None:
        return []

    base_domain = urlparse(base_url).netloc
    results: list[str] = []
    for link in page.links:
        parsed = urlparse(link)
        if parsed.netloc != base_domain:
            continue
        path_lower = parsed.path.lower()
        if any(hint in path_lower for hint in hints):
            results.append(link)
    return results[:5]


def extract_decision_makers_from_page(page: PageData) -> list[DecisionMakerCandidate]:
    candidates: list[DecisionMakerCandidate] = []
    role_keywords = ("ceo", "cto", "director", "manager", "president", "vp", "head", "chief", "engineer", "sales")

    for line in page.text.split("\n"):
        line = line.strip()
        if len(line) < 10 or len(line) > 200:
            continue
        lower = line.lower()
        if not any(kw in lower for kw in role_keywords):
            continue
        if "," in line:
            parts = [p.strip() for p in line.split(",", 1)]
            name, role = parts[0], parts[1] if len(parts) > 1 else None
        elif " - " in line:
            parts = [p.strip() for p in line.split(" - ", 1)]
            name, role = parts[0], parts[1] if len(parts) > 1 else None
        else:
            name, role = line[:80], None
        if 2 <= len(name.split()) <= 5:
            email = page.emails[0] if page.emails else None
            candidates.append(DecisionMakerCandidate(name=name[:255], role=role[:255] if role else None, email=email))

    return candidates[:10]
