# ReviewMind

AI-native PR review tool. Analyzes GitHub pull requests (and pasted/uploaded
code) for security and style issues, suggests concrete fixes, and can post
a review straight back to GitHub.

- **Backend** — FastAPI + MCP server (`reviewmind/`)
- **Frontend** — Next.js app (`frontend/`)

## Features

- Security scanning (hardcoded secrets, SQL injection, unsafe deserialization, etc.)
- Style scanning (naming, function length, docstrings, forbidden imports — configurable via `reviewmind.yaml`)
- Per-finding fix suggestions with an "Apply fix" flow
- GitHub PR analysis: diff, reviewers, review posting
- Chat interface backed by the Claude API, using the same analysis tools via MCP
- Supabase-backed auth

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Postgres + Redis (see `docker-compose.yml` for local instances)

### 1. Configure environment

Copy `.env.example` to `.env` in the repo root and fill in the values
(GitHub token, Anthropic API key, Supabase project, etc.). Both the
backend and the frontend read from this single root `.env` file — do not
create a separate `frontend/.env.local`.

```
cp .env.example .env
```

### 2. Start local infrastructure

```
docker-compose up -d
```

### 3. Run the backend

```
pip install -e ".[dev]"
alembic upgrade head
uvicorn reviewmind.api.main:app --reload
```

API is served at `http://localhost:8000`.

### 4. Run the frontend

```
cd frontend
npm install
npm run dev
```

App is served at `http://localhost:3000`.

## Testing

```
pytest
```

## Project layout

```
reviewmind/
  api/          FastAPI routes, auth, MCP tool wiring
  engine/       Diff parsing, security & style rule engines
  services/     PR analysis, fix suggestions, GitHub client, review posting
  core/         Config, logging, caching
  db/           SQLAlchemy models, Alembic migrations
frontend/
  app/          Next.js pages (analyze, PR review, compare, fix, chat)
  components/   Shared UI components
tests/          pytest suite + fixtures
```
