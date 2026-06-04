# Parijat Sales Intelligence Platform — Installation Guide

Install the platform on a Linux server (Ubuntu 22.04+ recommended) using Docker Compose.

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- Ports **3000** (frontend), **8000** (API), **5432** and **6379** (optional external access)
- **OpenAI API key** (approved paid service)
- **SMTP credentials** for Parijat mail server (campaign email)
- **Seed URLs** for lead discovery profiles

## Steps

### 1. Clone and configure

```bash
git clone <repository-url> sales-intelligence
cd sales-intelligence
cp .env.docker.example .env
```

Edit `.env`:

| Variable | Required | Notes |
|----------|----------|-------|
| `SECRET_KEY` | Yes | Long random string |
| `OPENAI_API_KEY` | Yes | For enrichment & AI messages |
| `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` | For email send | Set `SMTP_DRY_RUN=false` in production |
| `SMTP_FROM_EMAIL` | Yes | Verified sender on your domain |
| `NEXT_PUBLIC_API_URL` | Yes | Public API URL, e.g. `https://sales.parijat.com/api/v1` |

### 2. Start services

```bash
# Core stack
docker compose up -d postgres redis backend frontend

# Background workers (discovery crawl, enrichment, scheduled refresh)
docker compose --profile worker up -d
```

### 3. Verify health

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}`

### 4. First admin user

1. Open `http://<server>:3000/login` and sign up.
2. Promote to ADMIN via database (first install only):

```bash
docker exec -it sales-postgres psql -U salesapp -d salesapp \
  -c "UPDATE users SET role = 'ADMIN' WHERE email = 'you@parijat.com';"
```

### 5. Configure discovery

1. Log in as ADMIN or MANAGER.
2. Go to **Discovery** → create a profile with Parijat-provided seed URLs and industries.
3. Click **Run now** (requires Celery worker).

### 6. Production notes

- Use reverse proxy (nginx/Caddy) with TLS for frontend and API.
- Set `refresh_cookie_secure=true` and strong `SECRET_KEY`.
- Configure SPF/DKIM on sender domain for email deliverability.
- Back up PostgreSQL volume `postgres_data` regularly.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Celery worker not running | `docker compose --profile worker up -d celery-worker celery-beat` |
| Discovery returns 0 leads | Check seed URLs; ensure worker logs: `docker compose logs celery-worker` |
| Email not sending | Verify SMTP; check `SMTP_DRY_RUN=false` |
| Enrichment fails | Verify `OPENAI_API_KEY` in backend container env |

See also [operations.md](operations.md) and [third-party.md](third-party.md).
