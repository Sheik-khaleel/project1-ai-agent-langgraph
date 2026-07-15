# AI Agentic Demo using LangGraph

## Purpose
This repository showcases a deterministic, two-agent workflow that fetches todos from a public API and ingests them into an in-memory sink service. The goal is to provide a minimal, reproducible template for building LangGraph-driven orchestrators that coordinate specialized agents while keeping the implementation approachable for local development and containerized deployments.

## Scope
- **FetchAgent** downloads todos from JSONPlaceholder.
- **PostAgent** transforms todo records and persists them in the sink service.
- **Orchestrator** exposes a FastAPI endpoint (`POST /query`) that routes requests through the LangGraph graph.
- **Intent Parser** uses OpenAI Responses API with a rule-based fallback to recognize ingestion requests and limits.
- **Sink API** is a FastAPI app that stores records in memory and exposes health and retrieval endpoints.

The agents themselves rely on deterministic logic (no LLM calls) to maintain predictable behavior. Only the intent classifier optionally calls OpenAI.

## Tech Stack
- Python 3.12
- FastAPI + Uvicorn
- LangGraph
- httpx
- Pydantic
- OpenAI Python SDK (for optional intent classification)
- Docker & Docker Compose
- pytest (unit and integration tests)

## Repository Layout
```
.
├── orchestrator/
│   ├── app.py              # FastAPI entrypoint exposing /query
│   ├── graph.py            # LangGraph definition for FetchAgent & PostAgent
│   ├── intent.py           # Intent parsing with LLM fallback
│   ├── models.py           # Shared Pydantic models and state schema
│   ├── prompts.py          # Prompt templates (intent + agent context)
│   ├── tools.py            # HTTP helpers for fetch/sink interactions
│   ├── Dockerfile          # Uvicorn-based service image
│   └── requirements.txt
├── sink-api/
│   ├── main.py             # In-memory sink FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   ├── test_graph.py       # LangGraph unit coverage
│   ├── test_intent.py      # Intent parsing unit coverage
│   └── test_integration.py # Orchestrator↔sink integration tests
├── docker-compose.yml      # Multi-service orchestration
├── .env                    # Runtime environment variables (not committed)
├── .env.example            # Sample environment configuration
├── .gitignore              # Git ignore list
└── README.md               # Project documentation
```

## Prerequisites
- Docker Desktop **or** Python 3.12 with virtualenv tooling.
- OpenAI API key (if you want the LLM-powered intent classifier).

## Setup & Installation
1. **Clone the repository**
   ```bash
   git clone <repo_url>
   cd ai-agent
   ```
2. **Create an environment file**
   ```bash
   cp .env.example .env
   # edit .env with your OPENAI_API_KEY or leave placeholder for heuristic-only mode
   ```

### Option A: Run with Docker Compose
```bash
docker compose up --build
```
- Frontend available at `http://localhost:3000`.
- Orchestrator available at `http://localhost:8080`.
- Sink API available at `http://localhost:8000`.
- Stop with `Ctrl+C`, and clean up via `docker compose down`.

### Option B: Run Services Locally
1. Create and activate a virtual environment (recommended).
2. Install dependencies.
   ```bash
   pip install -r orchestrator/requirements.txt
   pip install -r sink-api/requirements.txt
   ```
3. Start the sink API.
   ```bash
   cd sink-api
   uvicorn main:app --reload --port 8000
   ```
4. Start the orchestrator in another shell.
   ```bash
   cd orchestrator
   uvicorn app:app --reload --port 8080
   ```
5. (Optional) Launch the React frontend.
   ```bash
   cd frontend
   npm install
   npm run dev -- --host 0.0.0.0 --port 3000
   ```
   Open `http://localhost:3000` in your browser.

## Usage
### Web UI
1. Start the stack (Docker or local).
2. Open `http://localhost:3000` to access the React client.
3. Enter a message (e.g., “please ingest todos 3”) and submit to trigger the orchestrator. The UI shows latest results plus recent history.

### API
You can still interact with the API directly for scripts or testing.

1. Ensure the services are running.
2. Send a request to the orchestrator.
   ```bash
   curl -X POST http://localhost:8080/query \
     -H "Content-Type: application/json" \
     -d '{"message": "please ingest todos 3"}'
   ```
3. Inspect persisted records.
   ```bash
   curl http://localhost:8000/records
   ```

If the message does not request todo ingestion, the orchestrator returns `400 Bad Request`. If the sink rejects the payload, the orchestrator surfaces a `502` with error details.

## Testing
Run tests after installing dependencies:
```bash
pytest -q
```
- `tests/test_intent.py` covers the intent classifier with and without LLM help.
- `tests/test_graph.py` validates graph behavior using stubbed tool functions.
- `tests/test_integration.py` spins up both FastAPI apps via `TestClient` to ensure end-to-end flow (success and failure paths).

## Configuration
Key environment variables (see `.env.example`):
- `OPENAI_API_KEY` – optional key for LLM intent classification.
- `OPENAI_MODEL` – defaults to `gpt-4o-mini`, only used when API key is provided.
- `FETCH_URL` – defaults to JSONPlaceholder todos endpoint.
- `SINK_URL` – defaults to internal Docker network URL for the sink.
- `VITE_API_BASE_URL` – overrides the frontend’s API target (defaults to `http://orchestrator:8080` in Docker and `http://localhost:8080` locally).

You can override these per environment, including at compose runtime via `docker compose run -e KEY=value`.

## Extending the Demo
- Add new LangGraph nodes (e.g., validation or enrichment) in `orchestrator/graph.py`.
- Introduce richer prompts while keeping the agents deterministic if desired.
- Persist records to an actual database by replacing the sink API implementation.
- Expand test coverage with additional scenarios (authorization, alternative sources, etc.).

## Support & Contributions
This project is intended as a reference implementation. Feel free to fork it, adapt it to your needs, and share improvements via pull requests or issues.
