from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_minimum_role
from src.common.database import get_db
from src.common.enums import LeadStatus, UserRole
from src.common.pagination import PaginatedResponse
from src.leads.schemas import (
    DecisionMakerCreate,
    DecisionMakerResponse,
    LeadCreate,
    LeadDetailResponse,
    LeadImportResult,
    LeadResponse,
    LeadUpdate,
)
from src.leads.search.schemas import (
    LeadSearchRequest,
    LeadSearchRunResponse,
    LeadSearchSaveRequest,
    LeadSearchSaveResponse,
    LeadSearchStartResponse,
)
from src.leads.search.service import LeadSearchService
from src.leads.service import LeadService
from src.users.models import User

router = APIRouter(prefix="/leads", tags=["leads"])

_sales_user = Depends(require_minimum_role(UserRole.SALES))


@router.get("", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    status: LeadStatus | None = None,
    industry: str | None = None,
    country: str | None = None,
) -> PaginatedResponse[LeadResponse]:
    service = LeadService(db)
    return await service.list_leads(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        industry=industry,
        country=country,
    )


@router.post("/import", response_model=LeadImportResult, status_code=status.HTTP_201_CREATED)
async def import_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
    file: Annotated[UploadFile, File(...)],
) -> LeadImportResult:
    content = (await file.read()).decode("utf-8-sig")
    service = LeadService(db)
    return await service.import_csv(current_user, content)


@router.get("/export")
async def export_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
    search: str | None = None,
    status: LeadStatus | None = None,
    industry: str | None = None,
    country: str | None = None,
) -> StreamingResponse:
    service = LeadService(db)
    csv_content = await service.export_csv(
        current_user,
        search=search,
        status=status,
        industry=industry,
        country=country,
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads.csv"'},
    )


@router.post("/search", response_model=LeadSearchStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_lead_search(
    payload: LeadSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadSearchStartResponse:
    return await LeadSearchService(db).start_search(current_user, payload)


@router.get("/search/{search_id}", response_model=LeadSearchRunResponse)
async def get_lead_search(
    search_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadSearchRunResponse:
    return await LeadSearchService(db).get_search_run(current_user, search_id)


@router.post("/search/{search_id}/save", response_model=LeadSearchSaveResponse)
async def save_lead_search_results(
    search_id: UUID,
    payload: LeadSearchSaveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadSearchSaveResponse:
    return await LeadSearchService(db).save_preview_leads(current_user, search_id, payload)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadResponse:
    service = LeadService(db)
    return await service.create_lead(current_user, payload)


@router.post("/{lead_id}/verify", response_model=LeadResponse)
async def verify_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadResponse:
    return await LeadService(db).verify_lead(current_user, lead_id)


@router.get("/duplicates", response_model=PaginatedResponse[LeadResponse])
async def list_duplicates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.MANAGER))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[LeadResponse]:
    return await LeadService(db).list_duplicates(current_user, page=page, page_size=page_size)


@router.delete("/duplicates/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_duplicate(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.MANAGER))],
) -> None:
    await LeadService(db).dismiss_duplicate(current_user, lead_id)


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadDetailResponse:
    service = LeadService(db)
    return await service.get_lead(current_user, lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> LeadResponse:
    service = LeadService(db)
    return await service.update_lead(current_user, lead_id, payload)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.MANAGER))],
) -> None:
    service = LeadService(db)
    await service.delete_lead(current_user, lead_id)


@router.get("/{lead_id}/decision-makers", response_model=list[DecisionMakerResponse])
async def list_decision_makers(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> list[DecisionMakerResponse]:
    service = LeadService(db)
    return await service.list_decision_makers(current_user, lead_id)


@router.post(
    "/{lead_id}/decision-makers",
    response_model=DecisionMakerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_decision_maker(
    lead_id: UUID,
    payload: DecisionMakerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> DecisionMakerResponse:
    service = LeadService(db)
    return await service.add_decision_maker(current_user, lead_id, payload)


@router.delete("/{lead_id}/decision-makers/{dm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_decision_maker(
    lead_id: UUID,
    dm_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> None:
    service = LeadService(db)
    await service.remove_decision_maker(current_user, lead_id, dm_id)
