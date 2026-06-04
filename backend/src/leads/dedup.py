"""Duplicate detection for leads."""

from __future__ import annotations

import uuid
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.url_utils import normalize_domain
from src.leads.models import Lead


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


async def find_duplicate(
    db: AsyncSession,
    *,
    company_name: str,
    website: str | None = None,
    email: str | None = None,
    exclude_id: uuid.UUID | None = None,
) -> Lead | None:
    domain = normalize_domain(website)
    email_lower = email.lower().strip() if email else None

    if domain:
        query = select(Lead).where(Lead.domain_normalized == domain, Lead.is_duplicate.is_(False))
        if exclude_id:
            query = query.where(Lead.id != exclude_id)
        existing = await db.scalar(query)
        if existing:
            return existing

    if email_lower:
        query = select(Lead).where(Lead.email.ilike(email_lower), Lead.is_duplicate.is_(False))
        if exclude_id:
            query = query.where(Lead.id != exclude_id)
        existing = await db.scalar(query)
        if existing:
            return existing

    query = select(Lead).where(Lead.is_duplicate.is_(False))
    if exclude_id:
        query = query.where(Lead.id != exclude_id)
    candidates = (await db.scalars(query.limit(500))).all()

    for candidate in candidates:
        if _similarity(company_name, candidate.company_name) >= 0.85:
            return candidate

    return None


def find_duplicate_sync(
    session,
    *,
    company_name: str,
    website: str | None = None,
    email: str | None = None,
) -> Lead | None:
    domain = normalize_domain(website)
    email_lower = email.lower().strip() if email else None

    if domain:
        existing = session.scalar(
            select(Lead).where(Lead.domain_normalized == domain, Lead.is_duplicate.is_(False))
        )
        if existing:
            return existing

    if email_lower:
        existing = session.scalar(
            select(Lead).where(Lead.email.ilike(email_lower), Lead.is_duplicate.is_(False))
        )
        if existing:
            return existing

    candidates = session.scalars(select(Lead).where(Lead.is_duplicate.is_(False)).limit(500)).all()
    for candidate in candidates:
        if _similarity(company_name, candidate.company_name) >= 0.85:
            return candidate
    return None
