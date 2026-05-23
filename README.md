# RePost AI

AI content repurposing agent for YouTube creators.

This repo starts with the Phase 0 foundation from `system-design.md`:

- FastAPI backend with `/health`
- Next.js + Tailwind frontend placeholder
- Docker Compose for Postgres and Redis
- Environment variable template for local development

## Local Development

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Infrastructure:

```powershell
docker compose up -d postgres redis
```

Expected checks:

```powershell
curl http://localhost:8000/health
```

Phase 2 local app:

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend
npm run dev
```

Phase 2 database migration:

```powershell
docker compose up -d postgres redis
psql "postgresql://repost:repost@localhost:5432/repost_ai" -f backend/app/db/migrations/0001_phase2_video_jobs.sql
```

Phase 2 worker queue:

```powershell
# Set USE_REDIS_QUEUE=true in backend/.env when Redis is running.
cd backend
arq app.worker.WorkerSettings
```

Phase 1 CLI contracts:

```powershell
cd backend
python -m agents.nodes.transcript --text "Paste transcript text here"
python run_pipeline.py --text "Paste transcript text here"
```

Install the transcript extra before fetching real YouTube transcripts:

```powershell
pip install -e ".[transcript]"
python -m agents.nodes.transcript "https://www.youtube.com/watch?v=VIDEO_ID"
```
