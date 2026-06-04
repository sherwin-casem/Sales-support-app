# Frontend

Next.js 15 frontend for the Sales Intelligence & AI Outreach Platform.

## Structure

```
frontend/
├── app/              # App Router pages & layouts
│   ├── (auth)/       # Login
│   ├── dashboard/
│   ├── leads/
│   ├── campaigns/
│   ├── analytics/
│   └── settings/
├── components/       # Shared UI components (shadcn/ui)
├── features/         # Feature-specific modules
├── lib/              # Utilities, hooks, theme
├── services/         # API client
└── types/            # TypeScript interfaces
```

## Phase Status

| Phase | Status |
|-------|--------|
| 1 — Structure | Complete |
| 3 — Frontend | In progress |
| 3a — Login, dashboard shell, KPIs, settings, dark mode | Complete |
| 3b — Leads UI (CRUD, import/export, detail) | Complete |
| 3c — Analytics page | Complete |
| 3d — Campaigns UI (preview) | Complete |

## Pages

| Path | Description |
|------|-------------|
| `/login` | Sign in / sign up |
| `/dashboard` | KPI overview, pipeline stats |
| `/leads` | Lead table, search, filters, CSV import/export |
| `/leads/[id]` | Lead detail & decision makers |
| `/campaigns` | Campaign preview (API pending) |
| `/analytics` | Pipeline analytics & funnel |
| `/settings` | Profile & theme |

## Local Development

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env` (project root).

App: http://localhost:3000
