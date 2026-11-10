# Luna AI Copilot

Luna is a production-minded AI hospitality operations copilot built with a local LLM, RAG, tool calling, human approval gates, persistent conversation state, analytics, and automated evaluations.

## Features

- Local LLM inference with Gemma via LM Studio
- Multi-step tool calling
- Retrieval-Augmented Generation for policies
- PostgreSQL-backed operational data
- Persistent conversation history
- Structured conversation state
- Human confirmation for sensitive actions
- Booking creation and cancellation
- Availability and pricing tools
- Usage analytics
- Automated evaluation suite
- React + TypeScript frontend
- FastAPI backend
- Alembic database migrations

## Architecture

React / TypeScript
        ↓
FastAPI
        ↓
AI Agent Orchestrator
   ├── Gemma
   ├── RAG
   ├── Tools
   ├── Approval Gates
   └── Conversation State
        ↓
PostgreSQL

## Agent Tools

Luna can currently:

- Retrieve booking details
- Check apartment availability
- Calculate quotes
- Create bookings
- Cancel bookings
- Retrieve hospitality policies

State-changing actions require explicit user confirmation.

## AI Safety

Luna is allowed to propose sensitive actions but cannot authorize them herself.

For example:

User → "Cancel booking 2"

Luna → proposes `cancel_booking`

Backend → stores pending action

User → Confirm / Reject

Backend → executes only after confirmation

## Evaluation

The project includes an automated evaluation suite covering:

- Tool selection
- Multi-step tool execution
- RAG grounding
- Sensitive-action approval
- Missing resource handling
- Latency

Eval reports are generated as JSON for regression tracking.
## Tech Stack
Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Psycopg
## AI
- Gemma
- LM Studio
- Nomic Embed Text
- RAG
- Tool Calling
## Frontend
- React
- TypeScript
- Vite
- Oxlint
## Running Locally
Backend
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload

## Frontend
cd frontend
npm install
npm run dev

## Services
The application also requires:
- PostgreSQL
- LM Studio local inference server
## Current Status
The current MVP supports real booking operations, conversational state, tool-based reasoning, human approval gates, analytics, and automated evaluations.

## Future work includes:
- CI/CD
- n8n workflow automation
- MCP integrations
- deployment
- richer observability
Run:

```bash
python evals/run_evals.py

