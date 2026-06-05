"""OpenAI integration for enrichment and message generation."""

from __future__ import annotations

import json

from openai import OpenAI

from src.common.config import Settings, get_settings
from src.scrapers.website import DecisionMakerCandidate

PARIJAT_CONTEXT = (
    "Parijat (parijat.com) provides controls and process automation solutions. "
    "Prioritize decision makers in engineering, operations, plant management, "
    "automation, instrumentation, and procurement roles."
)


def _client(settings: Settings | None = None) -> OpenAI | None:
    settings = settings or get_settings()
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def rank_decision_makers(
    candidates: list[DecisionMakerCandidate],
    company_name: str,
    settings: Settings | None = None,
) -> list[DecisionMakerCandidate]:
    if not candidates:
        return []
    client = _client(settings)
    if client is None:
        return candidates[:5]

    settings = settings or get_settings()
    payload = [{"name": c.name, "role": c.role, "email": c.email} for c in candidates]
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PARIJAT_CONTEXT},
                {
                    "role": "user",
                    "content": (
                        f"Rank these stakeholders at {company_name} for B2B sales outreach. "
                        f"Return JSON array of top 5 with name, role, email fields only:\n{json.dumps(payload)}"
                    ),
                },
            ],
            max_tokens=800,
            temperature=0.2,
        )
        content = response.choices[0].message.content or "[]"
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            result: list[DecisionMakerCandidate] = []
            for item in parsed:
                result.append(
                    DecisionMakerCandidate(
                        name=str(item.get("name", ""))[:255],
                        role=str(item.get("role", ""))[:255] if item.get("role") else None,
                        email=item.get("email"),
                    )
                )
            return [c for c in result if c.name]
    except Exception:
        pass
    return candidates[:5]


def infer_industry_from_text(text: str, settings: Settings | None = None) -> str | None:
    client = _client(settings)
    if client is None or not text.strip():
        return None
    settings = settings or get_settings()
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": f"Infer the primary industry (2-4 words) from this company text. Reply with industry only:\n{text[:3000]}",
                },
            ],
            max_tokens=30,
            temperature=0,
        )
        return (response.choices[0].message.content or "").strip()[:255] or None
    except Exception:
        return None


def generate_outreach_message(
    *,
    channel: str,
    company_name: str,
    contact_name: str | None,
    contact_role: str | None,
    industry: str | None,
    tone: str = "professional",
    extra_context: str | None = None,
    settings: Settings | None = None,
) -> tuple[str | None, str]:
    client = _client(settings)
    settings = settings or get_settings()
    contact = contact_name or "there"
    role_part = f" ({contact_role})" if contact_role else ""
    industry_part = industry or "their industry"

    prompt = (
        f"Write a {tone} {channel} outreach message for Parijat controls & process automation. "
        f"Target: {contact}{role_part} at {company_name} in {industry_part}. "
        f"Keep it concise and personalized. "
    )
    if extra_context:
        prompt += f"Context: {extra_context}. "
    if channel.upper() == "EMAIL":
        prompt += 'Return JSON: {"subject": "...", "body": "..."}'
    else:
        prompt += 'Return JSON: {"body": "..."}'

    if client is None:
        body = (
            f"Hello {contact},\n\n"
            f"I noticed {company_name}'s work in {industry_part} and wanted to connect regarding "
            f"process automation solutions from Parijat.\n\nBest regards"
        )
        subject = f"Process automation for {company_name}" if channel.upper() == "EMAIL" else None
        return subject, body

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PARIJAT_CONTEXT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        content = response.choices[0].message.content or "{}"
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            return data.get("subject"), str(data.get("body", ""))
    except Exception:
        pass
    return None, f"Hello {contact}, reaching out from Parijat regarding automation solutions for {company_name}."


def parse_lead_search_query(query: str, settings: Settings | None = None) -> dict:
    """Parse natural-language lead search into structured criteria."""
    settings = settings or get_settings()
    client = _client(settings)
    fallback = _fallback_parse_query(query)

    if client is None:
        return fallback

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PARIJAT_CONTEXT},
                {
                    "role": "user",
                    "content": (
                        "Parse this B2B lead search request into JSON with keys: "
                        "industries (array), countries (array), keywords (array), "
                        "company_signals (array), exclude_keywords (array), relevance_notes (string). "
                        f"Query: {query}"
                    ),
                },
            ],
            max_tokens=400,
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            return {
                "industries": parsed.get("industries") or [],
                "countries": parsed.get("countries") or [],
                "keywords": parsed.get("keywords") or [],
                "company_signals": parsed.get("company_signals") or [],
                "exclude_keywords": parsed.get("exclude_keywords") or [],
                "relevance_notes": parsed.get("relevance_notes") or "",
            }
    except Exception:
        pass
    return fallback


def build_web_search_queries(
    criteria: dict,
    original_query: str,
    settings: Settings | None = None,
) -> list[str]:
    """Build 1–3 Google search queries from parsed lead-search criteria."""
    settings = settings or get_settings()
    client = _client(settings)
    fallback = _fallback_web_search_queries(criteria, original_query)

    if client is None:
        return fallback

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PARIJAT_CONTEXT},
                {
                    "role": "user",
                    "content": (
                        "Generate 1 to 3 Google search queries to find B2B company websites matching "
                        "this lead search. Return JSON array of strings only. Focus on finding company "
                        f"homepages and industry directories.\nCriteria: {json.dumps(criteria)}\n"
                        f"Original request: {original_query}"
                    ),
                },
            ],
            max_tokens=200,
            temperature=0,
        )
        content = response.choices[0].message.content or "[]"
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            queries = [str(q).strip() for q in parsed if str(q).strip()]
            if queries:
                return queries[:3]
    except Exception:
        pass
    return fallback


def _fallback_web_search_queries(criteria: dict, original_query: str) -> list[str]:
    parts: list[str] = []
    parts.extend(criteria.get("keywords") or [])
    parts.extend(criteria.get("industries") or [])
    parts.extend(criteria.get("countries") or [])
    if parts:
        return [" ".join(parts[:8]) + " companies"]
    return [original_query.strip()[:200]]


def _fallback_parse_query(query: str) -> dict:
    words = [w.strip(".,!?") for w in query.lower().split() if len(w) > 3]
    return {
        "industries": [],
        "countries": [],
        "keywords": words[:10],
        "company_signals": [],
        "exclude_keywords": [],
        "relevance_notes": query[:500],
    }


def score_leads_against_criteria(
    candidates: list[dict],
    criteria: dict,
    settings: Settings | None = None,
    threshold: int = 40,
) -> list[dict]:
    """Score and filter candidate leads. Each candidate dict must have company_name, optional text fields."""
    if not candidates:
        return []

    settings = settings or get_settings()
    client = _client(settings)

    if client is None:
        return _fallback_score_leads(candidates, criteria, threshold)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PARIJAT_CONTEXT},
                {
                    "role": "user",
                    "content": (
                        f"Score each company 0-100 for this lead search criteria: {json.dumps(criteria)}. "
                        "Return JSON array of objects with company_name, match_score (int), match_reason (short string). "
                        f"Companies: {json.dumps(candidates[:50])}"
                    ),
                },
            ],
            max_tokens=2000,
            temperature=0.1,
        )
        content = response.choices[0].message.content or "[]"
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            scored = json.loads(content[start:end])
            by_name = {s.get("company_name", "").lower(): s for s in scored}
            result = []
            for cand in candidates:
                name_key = cand["company_name"].lower()
                score_data = by_name.get(name_key, {})
                score = int(score_data.get("match_score", 50))
                if score >= threshold:
                    result.append({
                        **cand,
                        "match_score": score,
                        "match_reason": str(score_data.get("match_reason", "Matched search criteria"))[:500],
                    })
            return sorted(result, key=lambda x: x["match_score"], reverse=True)
    except Exception:
        pass
    return _fallback_score_leads(candidates, criteria, threshold)


def _fallback_score_leads(candidates: list[dict], criteria: dict, threshold: int) -> list[dict]:
    keywords = [k.lower() for k in criteria.get("keywords", [])]
    industries = [i.lower() for i in criteria.get("industries", [])]
    countries = [c.lower() for c in criteria.get("countries", [])]
    result = []

    for cand in candidates:
        text = " ".join(
            str(cand.get(k, "") or "")
            for k in ("company_name", "industry", "country", "scraped_title", "website")
        ).lower()
        score = 30
        reasons = []
        for kw in keywords:
            if kw in text:
                score += 15
                reasons.append(kw)
        for ind in industries:
            if ind in text:
                score += 20
                reasons.append(ind)
        for country in countries:
            if country in text:
                score += 15
                reasons.append(country)
        score = min(score, 100)
        if score >= threshold:
            result.append({
                **cand,
                "match_score": score,
                "match_reason": f"Keyword match: {', '.join(reasons[:5])}" if reasons else "Partial match",
            })
    return sorted(result, key=lambda x: x["match_score"], reverse=True)
