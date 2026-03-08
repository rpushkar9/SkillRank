# SkillRank Frontend (Next.js)

This is the Next.js frontend for SkillRank search.

## Requirements

- Node.js 18+
- Running backend API (FastAPI) at `http://127.0.0.1:8000` by default

## Setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
```

## Run

```bash
npm run dev
```

Open `http://localhost:3000`.

## Backend Contract Used

The UI calls:

- `GET /api/v1/search?q=<query>&k=5`

Set backend URL in `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Notes

- Styling is intentionally migrated from the previous plain HTML UI.
- If frontend and backend are on different origins, backend must allow CORS for `http://localhost:3000`.
