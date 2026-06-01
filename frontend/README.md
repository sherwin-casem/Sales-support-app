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
| 3a — Dashboard shell, login, KPIs | Complete |

## Pages

| Path | Description |
|------|-------------|
| `/login` | Authentication |
| `/dashboard` | KPI overview, pipeline stats |
| `/leads` | Placeholder |
| `/campaigns` | Placeholder |
| `/analytics` | Placeholder |
| `/settings` | Profile & theme |

## Local Development

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env` (project root).

App: http://localhost:3000
