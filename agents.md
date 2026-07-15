# AGENTS.md for Python Agentic Demo

## Project Overview
This project is a minimal **agentic system** built with **Python, FastAPI, LangGraph, and OpenAI API**, orchestrating two agents:
- **FetchAgent** → retrieves data from a public API (JSONPlaceholder).
- **PostAgent** → transforms and posts data into a simple in-memory database (`sink-api`).

All components run as **Docker containers** using `docker-compose`.

**Structure:**
- **Main orchestrator logic**: `orchestrator/app.py`, `orchestrator/graph.py`
- **Agents**: implemented as LangGraph nodes in `graph.py`
- **Helper tools**: `orchestrator/tools.py`
- **Prompts**: `orchestrator/prompts.py`
- **Schemas/State**: `orchestrator/models.py`
- **Sink API**: `sink-api/main.py` (in-memory DB service)

---

## Setup Commands
To set up the development environment locally:

```shell
# 1. Clone repository
git clone <repo_url>
cd agentic-demo

# 2. Copy environment file and set secrets
cp .env.example .env
# Update OPENAI_API_KEY in .env

# 3. Start all services
docker compose up --build
```

Services:
- Orchestrator: `http://localhost:8080`
- Sink API: `http://localhost:8000`

---

## Dev Environment Tips
- **Python Environment**: Python 3.12 is recommended if running outside Docker.  
- **Dependencies**: Install locally with  
  ```shell
  pip install -r orchestrator/requirements.txt
  pip install -r sink-api/requirements.txt
  ```
- **Hot Reload**: For iterative work, run FastAPI apps directly with `uvicorn app:app --reload`.  
- **Environment Variables**: Managed via `.env` file. Key vars:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (default: `gpt-4o-mini`)
  - `FETCH_URL` (default: JSONPlaceholder todos)
  - `SINK_URL` (default: `http://sink-api:8000/records`)

---

## Coding Standards
- **Formatting**: Use `black` for code formatting, `ruff` for linting.
  ```shell
  black .
  ruff check .
  ```
- **Naming Conventions**:
  - snake_case for functions and variables.
  - PascalCase for Pydantic models and classes.
- **Type Hints**: All new code must include type annotations. Avoid `Any` unless required.
- **Separation of Concerns**:
  - Networking helpers live in `tools.py`
  - Prompts live in `prompts.py`
  - State and schemas live in `models.py`
- **No Inline Prompts**: Always define prompt templates in `prompts.py`.

---

## Testing Instructions
- **Running All Tests**:
  ```shell
  pytest -q
  ```
- **Local Testing**: Run orchestrator and sink API separately with `uvicorn`:
  ```shell
  cd orchestrator && uvicorn app:app --reload --port 8080
  cd sink-api && uvicorn main:app --reload --port 8000
  ```
- **Focused Testing**:
  ```shell
  pytest -k "test_router"
  ```
- **Expected End-to-End Test**:
  - POST `/query` to orchestrator with `{ "message": "please ingest todos" }`
  - Verify sink API `/records` contains 3–5 items with correct labels (`done` or `inbox`).

---

## Pull Request Conventions
- **Title Format**: `[Feat] Add router node`, `[Fix] Handle sink errors`, `[Chore] Update Dockerfile`
- **Description**:
  - Clear purpose of the change
  - Outline of implementation
  - **Testing Done** section (describe how functionality was verified)
- **Pre-Merge Requirements**:
  - All tests must pass
  - Code formatted (`black .`) and linted (`ruff check .`)
  - No hardcoded secrets in source code

---

## Contribution Workflow
- **Branch Naming**:  
  - `feat/*` → new features  
  - `fix/*` → bug fixes  
  - `chore/*` → housekeeping  
- **Commit Style**: Conventional commits with descriptive messages.  
- **Review Expectation**: At least one approval + CI passing before merge.

---

👉 This file acts as a **developer guide**: how to structure, run, and extend the orchestrator and its agents.
