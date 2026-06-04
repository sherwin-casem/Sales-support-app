from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.ai.openai_client import infer_industry_from_text, rank_decision_makers
from src.auth.rbac import has_minimum_role
from src.common.enums import LeadStatus, UserRole
from src.common.exceptions import NotFoundException
from src.common.url_utils import normalize_domain, normalize_website
from src.enrichment.models import EnrichmentRecord
from src.enrichment.schemas import (
    EnrichmentPreviewRequest,
    EnrichmentPreviewResponse,
    EnrichmentRecordResponse,
)
from src.intent.detector import detect_intent_signals, total_intent_score
from src.intent.models import IntentSignal
from src.leads.models import DecisionMaker, Lead
from src.scrapers.website import (
    CAREERS_PATH_HINTS,
    LEADERSHIP_PATH_HINTS,
    extract_decision_makers_from_page,
    fetch_page,
    find_subpages,
)
from src.users.models import User
from src.verification.email_phone import verify_email, verify_phone


class EnrichmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_lead(self, user: User, lead_id: uuid.UUID) -> Lead:
        query = select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.decision_makers))
        if not has_minimum_role(user.role, UserRole.MANAGER):
            query = query.where(Lead.created_by == user.id)
        lead = await self.db.scalar(query)
        if lead is None:
            raise NotFoundException("Lead not found", code="LEAD_NOT_FOUND")
        return lead

    async def list_history(self, user: User, lead_id: uuid.UUID) -> list[EnrichmentRecordResponse]:
        await self._get_lead(user, lead_id)
        records = (
            await self.db.scalars(
                select(EnrichmentRecord)
                .where(EnrichmentRecord.lead_id == lead_id)
                .order_by(EnrichmentRecord.enriched_at.desc())
            )
        ).all()
        return [EnrichmentRecordResponse.model_validate(r) for r in records]

    async def preview(self, user: User, payload: EnrichmentPreviewRequest) -> EnrichmentPreviewResponse:
        _ = user
        website = normalize_website(payload.website)
        domain = normalize_domain(website)
        title = description = industry = None
        dm_count = 0

        if website:
            page = fetch_page(website)
            if page:
                title = page.title
                description = page.description
                industry = infer_industry_from_text(page.text)
                for sub in find_subpages(website, LEADERSHIP_PATH_HINTS):
                    sub_page = fetch_page(sub)
                    if sub_page:
                        dm_count += len(extract_decision_makers_from_page(sub_page))

        return EnrichmentPreviewResponse(
            company_name=payload.company_name,
            domain=domain,
            scraped_title=title,
            scraped_description=description,
            inferred_industry=industry,
            decision_makers_found=dm_count,
        )

    async def enqueue_enrich(self, user: User, lead_id: uuid.UUID) -> str:
        lead = await self._get_lead(user, lead_id)
        from src.jobs.tasks import enrich_lead_task

        task = enrich_lead_task.delay(str(lead.id), str(user.id))
        return task.id

    async def enrich_lead_sync(self, lead_id: uuid.UUID) -> EnrichmentRecord | None:
        lead = await self.db.get(Lead, lead_id)
        if lead is None or not lead.website:
            return None

        website = normalize_website(lead.website)
        if not website:
            return None

        page = fetch_page(website)
        if page is None:
            return None

        industry = infer_industry_from_text(page.text) or lead.industry
        domain = normalize_domain(website)

        record = EnrichmentRecord(
            lead_id=lead.id,
            source="website_scrape",
            raw_data={"url": website, "emails": page.emails[:5], "phones": page.phones[:3]},
            domain=domain,
            scraped_title=page.title,
            scraped_description=page.description,
            inferred_industry=industry,
            enriched_at=datetime.now(UTC),
        )
        self.db.add(record)

        if industry:
            lead.industry = industry
        lead.domain_normalized = domain
        lead.status = LeadStatus.ENRICHED

        if page.emails and not lead.email:
            lead.email = page.emails[0]
        if page.phones and not lead.phone:
            lead.phone = page.phones[0]

        lead.email_verification_status = verify_email(lead.email)
        lead.phone_verification_status = verify_phone(lead.phone, lead.country or "US")

        all_candidates = []
        for sub in find_subpages(website, LEADERSHIP_PATH_HINTS):
            sub_page = fetch_page(sub)
            if sub_page:
                all_candidates.extend(extract_decision_makers_from_page(sub_page))

        ranked = rank_decision_makers(all_candidates, lead.company_name)
        existing_names = {dm.name.lower() for dm in lead.decision_makers}
        for candidate in ranked:
            if candidate.name.lower() not in existing_names:
                dm = DecisionMaker(
                    lead_id=lead.id,
                    name=candidate.name,
                    role=candidate.role,
                    email=candidate.email,
                    email_verification_status=verify_email(candidate.email),
                )
                self.db.add(dm)
                existing_names.add(candidate.name.lower())

        combined_text = page.text
        for sub in find_subpages(website, CAREERS_PATH_HINTS):
            sub_page = fetch_page(sub)
            if sub_page:
                combined_text += " " + sub_page.text

        for old_signal in list(lead.intent_signals):
            await self.db.delete(old_signal)
        signals = detect_intent_signals(combined_text)
        for sig in signals:
            self.db.add(
                IntentSignal(
                    lead_id=lead.id,
                    signal_type=sig.signal_type,
                    evidence=sig.evidence,
                    score=sig.score,
                    detected_at=datetime.now(UTC),
                )
            )
        lead.intent_score = total_intent_score(signals)

        await self.db.flush()
        await self.db.refresh(record)
        return record
