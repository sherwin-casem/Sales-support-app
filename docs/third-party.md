# Third-Party Services & Licenses

## Paid (requires Parijat approval)

| Service | Purpose | Cost model |
|---------|---------|------------|
| **OpenAI API** | Decision-maker ranking, industry inference, outreach message generation | Pay-per-token (~$5–50/mo dev) |

Configure via `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`.

## Parijat infrastructure (not third-party SaaS)

| Service | Purpose |
|---------|---------|
| **SMTP mail server** | Outbound campaign email via Parijat domain |
| **PostgreSQL / Redis** | Self-hosted in Docker |

## Open-source dependencies

All application code is custom-developed for Parijat. Dependencies:

- **Backend**: FastAPI, SQLAlchemy, Celery, Playwright, BeautifulSoup, httpx, dnspython, phonenumbers — see `backend/requirements.txt`
- **Frontend**: Next.js, React, Tailwind, Radix UI — see `frontend/package.json`

Licenses: MIT, BSD, Apache 2.0 (standard OSS).

## Not included (requires separate approval)

- LinkedIn / WhatsApp auto-send APIs
- Paid email verification (ZeroBounce, etc.)
- Commercial lead databases
- Google/Bing search APIs

LinkedIn and WhatsApp: **AI copy generation + manual copy/paste** only in current MVP.
