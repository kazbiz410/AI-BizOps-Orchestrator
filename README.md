# AI BizOps Orchestrator v0

AI BizOps Orchestrator v0 is an MVP for capturing business operations in natural language, decomposing them into structured steps, diagnosing inefficiencies, and generating recommendations, diagrams, interview questions, and implementation drafts.

## Repository structure

- `frontend/`: Next.js app for the product UI
- `backend/`: FastAPI app for APIs, orchestration logic, and AI integration
- `supabase/`: SQL schema and seed data for Hosted Supabase
- `product-prd.md`: product requirements source of truth
- `AGENTS.md`: working style and explanation rules for Codex

## Local development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Environment variables

Place `.env` at the repository root and fill in:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (recommended: `gemini-2.5-flash`)
- `SLACK_INCOMING_WEBHOOK_URL`

Notes:

- The backend loads `.env` from the repository root.
- `SUPABASE_URL` should be the project base URL. If `/rest/v1` is included, the backend normalizes it automatically.
- `gemini-2.5-flash` is the current recommended Gemini model for this repository. Earlier checks with `gemini-2.0-flash` hit free-tier quota errors in this environment, while `gemini-2.5-flash` succeeded with the same minimal request shape.
- `pytest` runs with `ENVIRONMENT=test`, so tests use in-memory storage instead of the real Supabase project.

## Connection status

The following real integrations have been verified in this repository:

- Supabase: real persistence confirmed after applying `supabase/schema.sql`
- Gemini: real generation confirmed with `GEMINI_MODEL=gemini-2.5-flash`
- Slack Incoming Webhook: real message delivery confirmed with a labeled test message

## Backend test

```bash
backend/.venv/bin/pytest backend/tests -q
```

## Current status

This repository currently contains an MVP implementation aligned to the PRD:

- monorepo structure with `frontend`, `backend`, and `supabase`
- CRUD APIs
- natural language decomposition API
- rule-based diagnosis API
- Gemini generation integration with verified real generation on `gemini-2.5-flash`
- Slack question generation integration with verified real webhook delivery
- Supabase schema SQL for hosted projects and verified real persistence
