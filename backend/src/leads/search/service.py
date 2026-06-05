from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import has_minimum_role
from src.common.enums import CrawlRunStatus, LeadSource, UserRole
from src.common.exceptions import ForbiddenException, NotFoundException
from src.common.url_utils import normalize_domain, normalize_website
from src.leads.dedup import find_duplicate
from src.leads.models import Lead
from src.leads.search.models import LeadSearchRun
from src.leads.search.schemas import (
    LeadPreviewItem,
    LeadSearchRequest,
    LeadSearchRunResponse,
    LeadSearchSaveRequest,
    LeadSearchSaveResponse,
    LeadSearchStartResponse,
)
from src.users.models import User
from src.verification.email_phone import verify_email, verify_phone


class LeadSearchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start_search(self, user: User, payload: LeadSearchRequest) -> LeadSearchStartResponse:
        run = LeadSearchRun(
            query_text=payload.query.strip(),
            seed_urls=[],
            created_by=user.id,
            status=CrawlRunStatus.PENDING,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)

        from src.jobs.tasks import run_lead_search_task

        task = run_lead_search_task.delay(str(run.id), payload.max_results)
        run.celery_task_id = task.id
        await self.db.flush()

        return LeadSearchStartResponse(search_id=run.id, task_id=task.id)

    async def get_search_run(self, user: User, search_id: uuid.UUID) -> LeadSearchRunResponse:
        run = await self._get_run_for_user(user, search_id)
        preview_items = [LeadPreviewItem.model_validate(item) for item in (run.preview_results or [])]
        return LeadSearchRunResponse(
            id=run.id,
            query_text=run.query_text,
            seed_urls=run.seed_urls,
            parsed_criteria=run.parsed_criteria or {},
            status=run.status.value,
            preview_items=preview_items,
            pages_crawled=run.pages_crawled,
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
        )

    async def save_preview_leads(
        self, user: User, search_id: uuid.UUID, payload: LeadSearchSaveRequest
    ) -> LeadSearchSaveResponse:
        run = await self._get_run_for_user(user, search_id)
        if run.status != CrawlRunStatus.COMPLETED:
            raise ForbiddenException("Search must complete before saving", code="SEARCH_NOT_COMPLETE")

        created = 0
        skipped = 0
        lead_ids: list[uuid.UUID] = []

        for item in payload.items:
            duplicate = await find_duplicate(
                self.db,
                company_name=item.company_name,
                website=item.website,
                email=item.email,
            )
            if duplicate:
                skipped += 1
                continue

            website = normalize_website(item.website)
            lead = Lead(
                company_name=item.company_name,
                website=website,
                email=item.email,
                phone=item.phone,
                country=item.country,
                industry=item.industry,
                source=LeadSource.SEARCH,
                domain_normalized=normalize_domain(website),
                created_by=user.id,
            )
            lead.email_verification_status = verify_email(item.email)
            lead.phone_verification_status = verify_phone(item.phone, item.country or "US")
            self.db.add(lead)
            await self.db.flush()
            await self.db.refresh(lead)
            lead_ids.append(lead.id)
            created += 1

            from src.jobs.tasks import enrich_lead_task

            enrich_lead_task.delay(str(lead.id), str(user.id))

        return LeadSearchSaveResponse(created=created, skipped=skipped, lead_ids=lead_ids)

    async def _get_run_for_user(self, user: User, search_id: uuid.UUID) -> LeadSearchRun:
        run = await self.db.get(LeadSearchRun, search_id)
        if run is None:
            raise NotFoundException("Search run not found", code="SEARCH_NOT_FOUND")
        if not has_minimum_role(user.role, UserRole.MANAGER) and run.created_by != user.id:
            raise ForbiddenException("Cannot access this search", code="FORBIDDEN")
        return run
