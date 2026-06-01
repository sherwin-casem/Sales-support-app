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
| 3 — Frontend implementation | Pending |

## Pages (Phase 3)

- Login
- Dashboard
- Leads (table, search, filter, pagination)
- Campaigns
- Analytics
- Settings (dark mode, profile)

## Local Development (Phase 3+)

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000
