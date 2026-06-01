# Database Schema

PostgreSQL 16 · Normalized · UUID primary keys · `created_at` / `updated_at` on all entities.

## Entity Relationship Diagram

```
users ─────────────┬────────────────── refresh_tokens
                   │
                   ├── leads ──────────┬── decision_makers
                   │                   └── enrichment_records
                   │
                   ├── campaigns ──────┬── campaign_leads ── campaign_messages
                   │                   │
                   └── generated_messages (optional campaign_id)

campaign_leads references leads + campaigns (unique pair)
```

## Enums

### `user_role`
`ADMIN`, `MANAGER`, `SALES`

### `lead_status`
`NEW`, `ENRICHED`, `CONTACTED`, `REPLIED`, `CONVERTED`

### `campaign_status`
`DRAFT`, `SCHEDULED`, `RUNNING`, `COMPLETED`, `PAUSED`

### `campaign_channel`
`EMAIL`, `LINKEDIN`, `WHATSAPP`

### `campaign_lead_status`
`PENDING`, `SENT`, `FAILED`, `REPLIED`, `CONVERTED`

### `message_channel`
`EMAIL`, `LINKEDIN`, `WHATSAPP`

## Tables

### `users`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| role | user_role | NOT NULL, default SALES |
| is_active | BOOLEAN | NOT NULL, default true |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() |

**Indexes:** `idx_users_email`, `idx_users_role`

### `refresh_tokens`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) ON DELETE CASCADE |
| token_hash | VARCHAR(255) | UNIQUE, NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| revoked_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_refresh_tokens_user_id`, `idx_refresh_tokens_token_hash`

### `leads`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| company_name | VARCHAR(255) | NOT NULL |
| website | VARCHAR(512) | NULL |
| email | VARCHAR(255) | NULL |
| phone | VARCHAR(50) | NULL |
| industry | VARCHAR(255) | NULL |
| employee_count | INTEGER | NULL |
| revenue | NUMERIC(15,2) | NULL |
| country | VARCHAR(100) | NULL |
| status | lead_status | NOT NULL, default NEW |
| created_by | UUID | FK → users(id) ON DELETE SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_leads_status`, `idx_leads_company_name`, `idx_leads_created_by`, `idx_leads_industry`, `idx_leads_country`

### `decision_makers`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| lead_id | UUID | FK → leads(id) ON DELETE CASCADE |
| name | VARCHAR(255) | NOT NULL |
| role | VARCHAR(255) | NULL |
| email | VARCHAR(255) | NULL |
| linkedin | VARCHAR(512) | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_decision_makers_lead_id`, `idx_decision_makers_role`

### `enrichment_records`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| lead_id | UUID | FK → leads(id) ON DELETE CASCADE |
| source | VARCHAR(100) | NOT NULL |
| raw_data | JSONB | NOT NULL, default '{}' |
| domain | VARCHAR(255) | NULL |
| scraped_title | VARCHAR(512) | NULL |
| scraped_description | TEXT | NULL |
| inferred_industry | VARCHAR(255) | NULL |
| inferred_employee_count | INTEGER | NULL |
| enriched_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_enrichment_records_lead_id`, `idx_enrichment_records_domain`

### `campaigns`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | NULL |
| status | campaign_status | NOT NULL, default DRAFT |
| channel | campaign_channel | NOT NULL, default EMAIL |
| scheduled_at | TIMESTAMPTZ | NULL |
| created_by | UUID | FK → users(id) ON DELETE SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_campaigns_status`, `idx_campaigns_created_by`, `idx_campaigns_scheduled_at`

### `campaign_leads`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| campaign_id | UUID | FK → campaigns(id) ON DELETE CASCADE |
| lead_id | UUID | FK → leads(id) ON DELETE CASCADE |
| status | campaign_lead_status | NOT NULL, default PENDING |
| sent_at | TIMESTAMPTZ | NULL |
| replied_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Constraints:** UNIQUE(campaign_id, lead_id)

**Indexes:** `idx_campaign_leads_campaign_id`, `idx_campaign_leads_lead_id`, `idx_campaign_leads_status`

### `campaign_messages`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| campaign_lead_id | UUID | FK → campaign_leads(id) ON DELETE CASCADE |
| subject | VARCHAR(512) | NULL |
| body | TEXT | NOT NULL |
| generated_by_ai | BOOLEAN | NOT NULL, default false |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_campaign_messages_campaign_lead_id`

### `generated_messages`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| lead_id | UUID | FK → leads(id) ON DELETE CASCADE |
| campaign_id | UUID | FK → campaigns(id) ON DELETE SET NULL |
| channel | message_channel | NOT NULL |
| subject | VARCHAR(512) | NULL |
| body | TEXT | NOT NULL |
| created_by | UUID | FK → users(id) ON DELETE SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Indexes:** `idx_generated_messages_lead_id`, `idx_generated_messages_campaign_id`, `idx_generated_messages_channel`

## Triggers

- `update_updated_at()` — BEFORE UPDATE trigger on all tables with `updated_at`

## Migration Strategy

- Alembic in `backend/` (Phase 2) with scripts mirrored in `database/migrations/`
- Initial migration: `database/migrations/001_initial_schema.sql`
- Seed script (optional): `database/seeds/001_admin_user.sql` (Phase 2)
