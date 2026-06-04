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
