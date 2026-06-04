from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import has_minimum_role
from src.common.enums import CrawlRunStatus, LeadSource, UserRole
from src.common.exceptions import ForbiddenException, NotFoundException
from src.common.url_utils import normalize_domain, normalize_website
from src.discovery.models import CrawlRun, DiscoveryProfile
from src.discovery.schemas import (
    CrawlRunResponse,
    DiscoveryProfileCreate,
    DiscoveryProfileResponse,
    DiscoveryProfileUpdate,
    RunDiscoveryResponse,
)
from src.leads.dedup import find_duplicate
from src.leads.models import Lead
from src.users.models import User


class DiscoveryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _can_manage(self, user: User) -> bool:
        return has_minimum_role(user.role, UserRole.MANAGER)

    async def list_profiles(self, user: User) -> list[DiscoveryProfileResponse]:
        query = select(DiscoveryProfile).order_by(DiscoveryProfile.created_at.desc())
        if not self._can_manage(user):
            query = query.where(DiscoveryProfile.created_by == user.id)
        profiles = (await self.db.scalars(query)).all()
        return [DiscoveryProfileResponse.model_validate(p) for p in profiles]

    async def get_profile(self, user: User, profile_id: uuid.UUID) -> DiscoveryProfileResponse:
        profile = await self._get_profile_for_user(user, profile_id)
        return DiscoveryProfileResponse.model_validate(profile)

    async def create_profile(self, user: User, payload: DiscoveryProfileCreate) -> DiscoveryProfileResponse:
        profile = DiscoveryProfile(
            **payload.model_dump(),
            created_by=user.id,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return DiscoveryProfileResponse.model_validate(profile)

    async def update_profile(
        self,
        user: User,
        profile_id: uuid.UUID,
        payload: DiscoveryProfileUpdate,
    ) -> DiscoveryProfileResponse:
        profile = await self._get_profile_for_user(user, profile_id)
        if not self._can_manage(user) and profile.created_by != user.id:
            raise ForbiddenException("Cannot update this profile", code="FORBIDDEN")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.db.flush()
        await self.db.refresh(profile)
        return DiscoveryProfileResponse.model_validate(profile)

    async def delete_profile(self, user: User, profile_id: uuid.UUID) -> None:
        if not self._can_manage(user):
            raise ForbiddenException("Only managers can delete profiles", code="INSUFFICIENT_ROLE")
        profile = await self._get_profile_for_user(user, profile_id)
        await self.db.delete(profile)

    async def list_runs(self, user: User, profile_id: uuid.UUID) -> list[CrawlRunResponse]:
        await self._get_profile_for_user(user, profile_id)
        runs = (
            await self.db.scalars(
                select(CrawlRun)
                .where(CrawlRun.profile_id == profile_id)
                .order_by(CrawlRun.created_at.desc())
                .limit(50)
            )
        ).all()
        return [CrawlRunResponse.model_validate(r) for r in runs]

    async def trigger_run(self, user: User, profile_id: uuid.UUID) -> RunDiscoveryResponse:
        profile = await self._get_profile_for_user(user, profile_id)
        if not profile.is_active:
            raise ForbiddenException("Profile is inactive", code="PROFILE_INACTIVE")

        crawl_run = CrawlRun(profile_id=profile.id, status=CrawlRunStatus.PENDING)
        self.db.add(crawl_run)
        await self.db.flush()
        await self.db.refresh(crawl_run)

        from src.jobs.tasks import crawl_discovery_profile

        task = crawl_discovery_profile.delay(str(crawl_run.id))
        crawl_run.celery_task_id = task.id
        await self.db.flush()

        return RunDiscoveryResponse(crawl_run_id=crawl_run.id, task_id=task.id)

    async def _get_profile_for_user(self, user: User, profile_id: uuid.UUID) -> DiscoveryProfile:
        profile = await self.db.get(DiscoveryProfile, profile_id)
        if profile is None:
            raise NotFoundException("Discovery profile not found", code="PROFILE_NOT_FOUND")
        if not self._can_manage(user) and profile.created_by != user.id:
            raise ForbiddenException("Cannot access this profile", code="FORBIDDEN")
        return profile

    @staticmethod
    async def create_lead_from_discovery(
        db: AsyncSession,
        *,
        company_name: str,
        website: str | None,
        email: str | None,
        phone: str | None,
        country: str | None,
        industry: str | None,
        profile_id: uuid.UUID,
        created_by: uuid.UUID | None,
    ) -> tuple[Lead | None, bool]:
        """Returns (lead, created). None lead if duplicate."""
        duplicate = await find_duplicate(db, company_name=company_name, website=website, email=email)
        if duplicate:
            dup_lead = Lead(
                company_name=company_name,
                website=normalize_website(website),
                email=email,
                phone=phone,
                country=country,
                industry=industry,
                source=LeadSource.DISCOVERY,
                domain_normalized=normalize_domain(website),
                discovery_profile_id=profile_id,
                created_by=created_by,
                is_duplicate=True,
                duplicate_of_id=duplicate.id,
            )
            db.add(dup_lead)
            await db.flush()
            return dup_lead, False

        lead = Lead(
            company_name=company_name,
            website=normalize_website(website),
            email=email,
            phone=phone,
            country=country,
            industry=industry,
            source=LeadSource.DISCOVERY,
            domain_normalized=normalize_domain(website),
            discovery_profile_id=profile_id,
            created_by=created_by,
        )
        db.add(lead)
        await db.flush()
        return lead, True
