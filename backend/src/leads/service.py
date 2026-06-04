import csv
import io
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.rbac import has_minimum_role
from src.common.enums import LeadSource, LeadStatus, UserRole
from src.common.url_utils import normalize_domain, normalize_website
from src.leads.dedup import find_duplicate
from src.verification.email_phone import verify_email, verify_phone
from src.common.exceptions import ForbiddenException, NotFoundException
from src.common.pagination import PaginatedResponse
from src.leads.models import DecisionMaker, Lead
from src.leads.schemas import (
    DecisionMakerCreate,
    DecisionMakerResponse,
    LeadCreate,
    LeadDetailResponse,
    LeadImportResult,
    LeadResponse,
    LeadUpdate,
)
from src.users.models import User

CSV_COLUMNS = [
    "company_name",
    "website",
    "email",
    "phone",
    "industry",
    "employee_count",
    "revenue",
    "country",
    "status",
]

EXPORT_COLUMNS = ["id", *CSV_COLUMNS, "created_at", "updated_at"]


class LeadService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _can_access_all(self, user: User) -> bool:
        return has_minimum_role(user.role, UserRole.MANAGER)

    def _apply_access_filter(self, query, user: User):
        if self._can_access_all(user):
            return query
        return query.where(Lead.created_by == user.id)

    async def _get_lead_for_user(self, user: User, lead_id: UUID) -> Lead:
        query = select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.decision_makers))
        query = self._apply_access_filter(query, user)
        lead = await self.db.scalar(query)
        if lead is None:
            raise NotFoundException("Lead not found", code="LEAD_NOT_FOUND")
        return lead

    async def list_leads(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: LeadStatus | None = None,
        industry: str | None = None,
        country: str | None = None,
    ) -> PaginatedResponse[LeadResponse]:
        query = select(Lead)
        query = self._apply_access_filter(query, user)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Lead.company_name.ilike(pattern),
                    Lead.email.ilike(pattern),
                    Lead.website.ilike(pattern),
                )
            )
        if status:
            query = query.where(Lead.status == status)
        if industry:
            query = query.where(Lead.industry.ilike(f"%{industry.strip()}%"))
        if country:
            query = query.where(Lead.country.ilike(f"%{country.strip()}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        query = query.order_by(Lead.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        leads = (await self.db.scalars(query)).all()

        items = [LeadResponse.model_validate(lead) for lead in leads]
        return PaginatedResponse.build(items, total, page, page_size)

    async def get_lead(self, user: User, lead_id: UUID) -> LeadDetailResponse:
        lead = await self._get_lead_for_user(user, lead_id)
        return LeadDetailResponse.model_validate(lead)

    async def create_lead(self, user: User, payload: LeadCreate) -> LeadResponse:
        website = normalize_website(payload.website)
        duplicate = await find_duplicate(
            self.db,
            company_name=payload.company_name,
            website=website,
            email=str(payload.email) if payload.email else None,
        )
        lead = Lead(
            **payload.model_dump(mode="json"),
            website=website,
            domain_normalized=normalize_domain(website),
            created_by=user.id,
            source=LeadSource.MANUAL,
            is_duplicate=duplicate is not None,
            duplicate_of_id=duplicate.id if duplicate else None,
        )
        lead.email_verification_status = verify_email(str(payload.email) if payload.email else None)
        lead.phone_verification_status = verify_phone(payload.phone, payload.country or "US")
        self.db.add(lead)
        await self.db.flush()
        await self.db.refresh(lead)
        return LeadResponse.model_validate(lead)

    async def update_lead(self, user: User, lead_id: UUID, payload: LeadUpdate) -> LeadResponse:
        lead = await self._get_lead_for_user(user, lead_id)
        updates = payload.model_dump(exclude_unset=True, mode="json")
        for field, value in updates.items():
            setattr(lead, field, value)
        await self.db.flush()
        await self.db.refresh(lead)
        return LeadResponse.model_validate(lead)

    async def delete_lead(self, user: User, lead_id: UUID) -> None:
        if not self._can_access_all(user):
            raise ForbiddenException("Only managers can delete leads", code="INSUFFICIENT_ROLE")
        lead = await self._get_lead_for_user(user, lead_id)
        await self.db.delete(lead)

    async def list_decision_makers(self, user: User, lead_id: UUID) -> list[DecisionMakerResponse]:
        lead = await self._get_lead_for_user(user, lead_id)
        return [DecisionMakerResponse.model_validate(dm) for dm in lead.decision_makers]

    async def add_decision_maker(
        self,
        user: User,
        lead_id: UUID,
        payload: DecisionMakerCreate,
    ) -> DecisionMakerResponse:
        lead = await self._get_lead_for_user(user, lead_id)
        decision_maker = DecisionMaker(lead_id=lead.id, **payload.model_dump(mode="json"))
        self.db.add(decision_maker)
        await self.db.flush()
        await self.db.refresh(decision_maker)
        return DecisionMakerResponse.model_validate(decision_maker)

    async def remove_decision_maker(self, user: User, lead_id: UUID, dm_id: UUID) -> None:
        await self._get_lead_for_user(user, lead_id)
        decision_maker = await self.db.scalar(
            select(DecisionMaker).where(DecisionMaker.id == dm_id, DecisionMaker.lead_id == lead_id)
        )
        if decision_maker is None:
            raise NotFoundException("Decision maker not found", code="DECISION_MAKER_NOT_FOUND")
        await self.db.delete(decision_maker)

    async def import_csv(self, user: User, content: str) -> LeadImportResult:
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return LeadImportResult(created=0, failed=0, errors=["CSV file is empty or missing headers"])

        created = 0
        failed = 0
        errors: list[str] = []

        for row_num, row in enumerate(reader, start=2):
            try:
                company_name = (row.get("company_name") or "").strip()
                if not company_name:
                    raise ValueError("company_name is required")

                status_raw = (row.get("status") or "NEW").strip().upper()
                status = LeadStatus(status_raw) if status_raw else LeadStatus.NEW

                employee_count = _parse_optional_int(row.get("employee_count"))
                revenue = _parse_optional_decimal(row.get("revenue"))

                lead = Lead(
                    company_name=company_name,
                    website=_empty_to_none(row.get("website")),
                    email=_empty_to_none(row.get("email")),
                    phone=_empty_to_none(row.get("phone")),
                    industry=_empty_to_none(row.get("industry")),
                    employee_count=employee_count,
                    revenue=revenue,
                    country=_empty_to_none(row.get("country")),
                    status=status,
                    created_by=user.id,
                )
                self.db.add(lead)
                created += 1
            except (ValueError, KeyError) as exc:
                failed += 1
                errors.append(f"Row {row_num}: {exc}")

        if created:
            await self.db.flush()

        return LeadImportResult(created=created, failed=failed, errors=errors)

    async def export_csv(
        self,
        user: User,
        *,
        search: str | None = None,
        status: LeadStatus | None = None,
        industry: str | None = None,
        country: str | None = None,
    ) -> str:
        result = await self.list_leads(
            user,
            page=1,
            page_size=100,
            search=search,
            status=status,
            industry=industry,
            country=country,
        )

        # Fetch all pages for export
        all_leads: list[LeadResponse] = list(result.items)
        for page in range(2, result.pages + 1):
            page_result = await self.list_leads(
                user,
                page=page,
                page_size=100,
                search=search,
                status=status,
                industry=industry,
                country=country,
            )
            all_leads.extend(page_result.items)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for lead in all_leads:
            writer.writerow(
                {
                    "id": str(lead.id),
                    "company_name": lead.company_name,
                    "website": lead.website or "",
                    "email": lead.email or "",
                    "phone": lead.phone or "",
                    "industry": lead.industry or "",
                    "employee_count": lead.employee_count if lead.employee_count is not None else "",
                    "revenue": str(lead.revenue) if lead.revenue is not None else "",
                    "country": lead.country or "",
                    "status": lead.status.value,
                    "created_at": lead.created_at.isoformat(),
                    "updated_at": lead.updated_at.isoformat(),
                }
            )
        return output.getvalue()

    async def verify_lead(self, user: User, lead_id: UUID) -> LeadResponse:
        lead = await self._get_lead_for_user(user, lead_id)
        lead.email_verification_status = verify_email(lead.email)
        lead.phone_verification_status = verify_phone(lead.phone, lead.country or "US")
        from datetime import UTC, datetime

        if lead.email_verification_status.value in ("MX_FOUND", "VALID_FORMAT"):
            lead.email_verified_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(lead)
        return LeadResponse.model_validate(lead)

    async def list_duplicates(self, user: User, page: int = 1, page_size: int = 20) -> PaginatedResponse[LeadResponse]:
        query = select(Lead).where(Lead.is_duplicate.is_(True))
        query = self._apply_access_filter(query, user)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        leads = (await self.db.scalars(query)).all()
        items = [LeadResponse.model_validate(lead) for lead in leads]
        return PaginatedResponse.build(items, total, page, page_size)

    async def dismiss_duplicate(self, user: User, lead_id: UUID) -> None:
        if not self._can_access_all(user):
            raise ForbiddenException("Only managers can dismiss duplicates", code="INSUFFICIENT_ROLE")
        lead = await self._get_lead_for_user(user, lead_id)
        if not lead.is_duplicate:
            raise NotFoundException("Not a duplicate record", code="NOT_DUPLICATE")
        await self.db.delete(lead)


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or not str(value).strip():
        return None
    return int(str(value).strip())


def _parse_optional_decimal(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid revenue value: {value}") from exc
