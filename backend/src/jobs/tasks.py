"""Celery background tasks."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from src.common.enums import CrawlRunStatus, LeadSource
from src.common.sync_database import get_sync_db
from src.common.url_utils import normalize_domain, normalize_website
from src.discovery.models import CrawlRun, DiscoveryProfile
from src.jobs.celery_app import celery_app
from src.leads.dedup import find_duplicate_sync
from src.leads.models import Lead
from src.scrapers.website import crawl_seed_urls


@celery_app.task(name="health.ping")
def health_ping() -> str:
    return "pong"


@celery_app.task(name="leads.run_search", bind=True)
def run_lead_search_task(self, search_run_id: str, max_results: int = 20) -> dict:
    run_uuid = uuid.UUID(search_run_id)
    with get_sync_db() as session:
        from src.leads.search.models import LeadSearchRun
        from src.leads.search.pipeline import run_search_pipeline

        run = session.get(LeadSearchRun, run_uuid)
        if run is None:
            return {"error": "search_run_not_found"}

        run.status = CrawlRunStatus.RUNNING
        run.started_at = datetime.now(UTC)
        run.celery_task_id = self.request.id

        try:
            criteria, preview_items, pages, discovered_urls = run_search_pipeline(
                run.query_text,
                max_results=max_results,
                session=session,
            )
            run.parsed_criteria = criteria.model_dump()
            run.preview_results = [item.model_dump(mode="json") for item in preview_items]
            run.seed_urls = discovered_urls
            run.pages_crawled = pages
            run.status = CrawlRunStatus.COMPLETED
            run.completed_at = datetime.now(UTC)
            return {
                "pages_crawled": pages,
                "preview_count": len(preview_items),
                "discovered_urls": len(discovered_urls),
            }
        except Exception as exc:
            run.status = CrawlRunStatus.FAILED
            run.error_message = str(exc)[:2000]
            run.completed_at = datetime.now(UTC)
            raise


@celery_app.task(name="discovery.crawl_profile", bind=True)
def crawl_discovery_profile(self, crawl_run_id: str) -> dict:
    run_uuid = uuid.UUID(crawl_run_id)
    with get_sync_db() as session:
        crawl_run = session.get(CrawlRun, run_uuid)
        if crawl_run is None:
            return {"error": "crawl_run_not_found"}

        profile = session.get(DiscoveryProfile, crawl_run.profile_id)
        if profile is None:
            crawl_run.status = CrawlRunStatus.FAILED
            crawl_run.error_message = "Profile not found"
            return {"error": "profile_not_found"}

        crawl_run.status = CrawlRunStatus.RUNNING
        crawl_run.started_at = datetime.now(UTC)
        crawl_run.celery_task_id = self.request.id

        try:
            extracted, pages = crawl_seed_urls(
                profile.seed_urls,
                min(profile.max_pages, 500),
                profile.crawl_depth,
                profile.industries or [],
                profile.countries or [],
            )
            crawl_run.pages_crawled = pages
            crawl_run.leads_found = len(extracted)
            created_count = 0

            for item in extracted:
                duplicate = find_duplicate_sync(
                    session,
                    company_name=item.company_name,
                    website=item.website,
                    email=item.email,
                )
                industry = profile.industries[0] if profile.industries else None
                if duplicate:
                    lead = Lead(
                        company_name=item.company_name,
                        website=normalize_website(item.website),
                        email=item.email,
                        phone=item.phone,
                        country=item.country or (profile.countries[0] if profile.countries else None),
                        industry=industry,
                        source=LeadSource.DISCOVERY,
                        domain_normalized=normalize_domain(item.website),
                        discovery_profile_id=profile.id,
                        created_by=profile.created_by,
                        is_duplicate=True,
                        duplicate_of_id=duplicate.id,
                    )
                    session.add(lead)
                else:
                    lead = Lead(
                        company_name=item.company_name,
                        website=normalize_website(item.website),
                        email=item.email,
                        phone=item.phone,
                        country=item.country or (profile.countries[0] if profile.countries else None),
                        industry=industry,
                        source=LeadSource.DISCOVERY,
                        domain_normalized=normalize_domain(item.website),
                        discovery_profile_id=profile.id,
                        created_by=profile.created_by,
                    )
                    session.add(lead)
                    created_count += 1

            profile.last_run_at = datetime.now(UTC)
            crawl_run.leads_created = created_count
            crawl_run.status = CrawlRunStatus.COMPLETED
            crawl_run.completed_at = datetime.now(UTC)
            return {
                "pages_crawled": pages,
                "leads_found": len(extracted),
                "leads_created": created_count,
            }
        except Exception as exc:
            crawl_run.status = CrawlRunStatus.FAILED
            crawl_run.error_message = str(exc)[:2000]
            crawl_run.completed_at = datetime.now(UTC)
            raise


@celery_app.task(name="enrichment.enrich_lead")
def enrich_lead_task(lead_id: str, user_id: str) -> dict:
    async def _run() -> dict:
        from src.common.database import AsyncSessionLocal
        from src.enrichment.service import EnrichmentService

        async with AsyncSessionLocal() as db:
            service = EnrichmentService(db)
            record = await service.enrich_lead_sync(uuid.UUID(lead_id))
            await db.commit()
            return {"enriched": record is not None, "record_id": str(record.id) if record else None}

    return asyncio.run(_run())


@celery_app.task(name="discovery.refresh_stale_leads")
def refresh_stale_leads() -> dict:
    """Re-enqueue enrichment for leads older than 30 days."""
    from datetime import timedelta

    cutoff = datetime.now(UTC) - timedelta(days=30)
    count = 0
    with get_sync_db() as session:
        leads = session.scalars(
            select(Lead).where(
                Lead.website.isnot(None),
                Lead.is_duplicate.is_(False),
                Lead.updated_at < cutoff,
            ).limit(50)
        ).all()
        for lead in leads:
            enrich_lead_task.delay(str(lead.id), str(lead.created_by or ""))
            count += 1
    return {"enqueued": count}


@celery_app.task(name="campaigns.send_email")
def send_campaign_email_task(campaign_lead_id: str) -> dict:
    from src.campaigns.email_sender import send_campaign_lead_email

    return send_campaign_lead_email(uuid.UUID(campaign_lead_id))
