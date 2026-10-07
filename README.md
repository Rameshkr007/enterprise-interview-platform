# Enterprise AI-Powered Mock Interview & Semantic ATS Analyzer

## Architecture

- **Frontend**: Next.js 15 (App Router), TailwindCSS, TypeScript, WebSockets
- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL 16 + PGVector
- **AI/ML**: LangGraph (stateful interview agent), OpenAI Whisper (STT), Librosa/SciPy (audio analytics), GPT-4o
- **Infrastructure**: Redis (session state), MinIO (object storage), NGINX (reverse proxy)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### 1. Clone & Configure

```bash
cd enterprise-interview-platform
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY and SECRET_KEY
```

### 2. Launch with Docker Compose

```bash
docker compose up -d
```

### 3. Run Database Migrations

```bash
docker exec interview_backend alembic upgrade head
```

### 4. Create MinIO Bucket

```bash
# Open MinIO console at http://localhost:9001
# Credentials: minioadmin / minioadmin
# Create bucket named: interview-platform
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/docs
- MinIO Console: http://localhost:9001

## Local Development (without Docker)

### Backend

```bash
cd backend
pip install -e .
cp .env.example .env  # Configure your .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login, get JWT |
| GET  | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/ats/resume` | Upload resume (PDF) |
| POST | `/api/v1/ats/job-description` | Create JD |
| POST | `/api/v1/ats/analyze` | Run semantic ATS analysis |
| POST | `/api/v1/interview/session` | Create interview session |
| POST | `/api/v1/interview/answer` | Submit answer (audio b64) |
| POST | `/api/v1/reports/generate/{id}` | Generate session report |
| WS   | `/ws/interview/{session_id}?token=JWT` | Real-time interview stream |

## Key Design Decisions

1. **PGVector HNSW** (`m=16, ef_construction=64`) for sub-ms ANN search on resume/JD embeddings
2. **LangGraph MemorySaver** checkpointed to Redis for stateful multi-turn interview sessions
3. **Librosa pyin** for F0 pitch extraction; coefficient of variation as confidence score proxy
4. **GPT-4o JSON mode** for structured rubric evaluation — no prompt injection risk
5. **asyncio.Queue** for streaming Whisper chunks with backpressure control
6. **NGINX rate limiting**: 60 req/min for API, 10 req/min for WebSocket upgrades
