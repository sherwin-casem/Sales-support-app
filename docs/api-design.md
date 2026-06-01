# API Design — `/api/v1`

Base URL: `http://localhost:8000/api/v1`

OpenAPI: `http://localhost:8000/docs`

All protected routes require `Authorization: Bearer <access_token>` unless noted.

## Auth `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/signup` | Public | Register user (default role SALES) |
| POST | `/auth/login` | Public | Returns access token; sets refresh cookie |
| POST | `/auth/refresh` | Cookie | Rotate access token |
| POST | `/auth/logout` | Bearer | Revoke refresh token |
| GET | `/auth/me` | Bearer | Current user profile |

## Users `/users`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/users` | ADMIN, MANAGER | List users (paginated) |
| GET | `/users/{id}` | ADMIN, MANAGER | Get user |
| PATCH | `/users/{id}` | ADMIN | Update role/status |
| DELETE | `/users/{id}` | ADMIN | Deactivate user |

## Leads `/leads`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/leads` | SALES+ | List with search, filter, pagination |
| POST | `/leads` | SALES+ | Create lead |
| GET | `/leads/{id}` | SALES+ | Get lead with decision makers |
| PATCH | `/leads/{id}` | SALES+ | Update lead |
| DELETE | `/leads/{id}` | MANAGER+ | Delete lead |
| POST | `/leads/import` | SALES+ | CSV import (multipart) |
| GET | `/leads/export` | SALES+ | CSV export |
| GET | `/leads/{id}/decision-makers` | SALES+ | List decision makers |
| POST | `/leads/{id}/decision-makers` | SALES+ | Add decision maker |
| DELETE | `/leads/{id}/decision-makers/{dm_id}` | SALES+ | Remove decision maker |

**Query params (list):** `page`, `page_size`, `search`, `status`, `industry`, `country`

## Enrichment `/enrichment`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/enrichment/leads/{id}` | SALES+ | Enqueue full enrichment job |
| POST | `/enrichment/preview` | SALES+ | Sync preview from website/name |
| GET | `/enrichment/leads/{id}` | SALES+ | Enrichment history for lead |
| GET | `/enrichment/jobs/{job_id}` | SALES+ | Job status |

## Messages `/messages`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/messages/generate` | SALES+ | AI generate personalized message |
| GET | `/messages` | SALES+ | List generated messages (filter by lead/campaign) |
| GET | `/messages/{id}` | SALES+ | Get message |

**POST `/messages/generate` body:**
```json
{
  "lead_id": "uuid",
  "channel": "email | linkedin | whatsapp",
  "campaign_id": "uuid | null",
  "tone": "professional",
  "context": "optional extra context"
}
```

## Campaigns `/campaigns`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/campaigns` | SALES+ | List campaigns |
| POST | `/campaigns` | SALES+ | Create campaign |
| GET | `/campaigns/{id}` | SALES+ | Campaign detail with leads |
| PATCH | `/campaigns/{id}` | SALES+ | Update campaign |
| DELETE | `/campaigns/{id}` | MANAGER+ | Delete campaign |
| POST | `/campaigns/{id}/leads` | SALES+ | Add leads (bulk) |
| DELETE | `/campaigns/{id}/leads/{lead_id}` | SALES+ | Remove lead |
| POST | `/campaigns/{id}/schedule` | SALES+ | Schedule send |
| POST | `/campaigns/{id}/send` | MANAGER+ | Trigger immediate send |
| PATCH | `/campaigns/{id}/leads/{lead_id}/status` | SALES+ | Update lead campaign status |

## Analytics `/analytics`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/analytics/overview` | SALES+ | Dashboard KPIs |
| GET | `/analytics/campaigns/{id}` | SALES+ | Campaign-specific metrics |

**Overview response:**
```json
{
  "total_leads": 0,
  "total_campaigns": 0,
  "sent_messages": 0,
  "reply_rate": 0.0,
  "conversion_rate": 0.0,
  "leads_by_status": {}
}
```

## Common Conventions

- **Pagination:** `{ "items": [], "total": 0, "page": 1, "page_size": 20, "pages": 0 }`
- **Errors:** `{ "detail": "message", "code": "ERROR_CODE" }`
- **IDs:** UUID v4
- **Timestamps:** ISO 8601 UTC

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | Public | Service health (no version prefix) |
