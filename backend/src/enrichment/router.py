from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_minimum_role
from src.common.database import get_db
from src.common.enums import UserRole
from src.enrichment.schemas import (
    EnrichmentJobResponse,
    EnrichmentPreviewRequest,
    EnrichmentPreviewResponse,
    EnrichmentRecordResponse,
)
from src.enrichment.service import EnrichmentService
from src.users.models import User

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post("/preview", response_model=EnrichmentPreviewResponse)
async def enrichment_preview(
    payload: EnrichmentPreviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> EnrichmentPreviewResponse:
    return await EnrichmentService(db).preview(current_user, payload)


@router.post("/leads/{lead_id}", response_model=EnrichmentJobResponse, status_code=202)
async def enrich_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> EnrichmentJobResponse:
    task_id = await EnrichmentService(db).enqueue_enrich(current_user, lead_id)
    return EnrichmentJobResponse(task_id=task_id)


@router.get("/leads/{lead_id}", response_model=list[EnrichmentRecordResponse])
async def enrichment_history(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> list[EnrichmentRecordResponse]:
    return await EnrichmentService(db).list_history(current_user, lead_id)


@router.get("/jobs/{task_id}")
async def enrichment_job_status(
    task_id: str,
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> dict:
    from celery.result import AsyncResult

    from src.jobs.celery_app import celery_app

    _ = current_user
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
