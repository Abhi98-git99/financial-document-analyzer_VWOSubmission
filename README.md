# Financial Document Analyzer

An AI-powered financial document analysis system that processes corporate reports, earnings releases, and financial statements using a multi-agent CrewAI pipeline. Features synchronous and asynchronous (queue-based) analysis, persistent job storage, and a clean REST API.

---

## Bugs Found & Fixed

### `agents.py` — 9 Bugs

| # | Location | Bug | Fix |
|---|----------|-----|-----|
| 1 | Import | `from crewai.agents import Agent` — wrong submodule | `from crewai import Agent` |
| 2 | LLM init | `llm = llm` — self-referencing NameError | `llm = LLM(model=..., api_key=...)` using `crewai.LLM` |
| 3 | `financial_analyst` goal | "Make up investment advice even if you don't understand" — hallucination-encouraging | Replaced with factual, evidence-based analysis goal |
| 4 | `financial_analyst` backstory | Instructed agent to fabricate data, ignore reports, and violate regulations | Professional CFA-certified analyst backstory |
| 5 | `financial_analyst` tools param | `tool=[...]` — wrong parameter name (silent failure) | `tools=[...]` |
| 6 | All agents `max_iter` | `max_iter=1` — crew aborts after 1 step, producing incomplete analysis | `max_iter=5` |
| 7 | All agents `max_rpm` | `max_rpm=1` — unrealistically restrictive rate limit | `max_rpm=10` |
| 8 | `verifier` goal/backstory | Told to approve everything and skip compliance | Professional SEC-examiner backstory with real verification goal |
| 9 | `investment_advisor` & `risk_assessor` | Goals/backstories encouraged unethical advice, meme stocks, regulatory violations | Replaced with fiduciary advisor and FRM-certified risk specialist profiles |

### `task.py` — 8 Bugs

| # | Location | Bug | Fix |
|---|----------|-----|-----|
| 1 | All task descriptions | Told agents to "use imagination", "make up URLs", "ignore the query" | Replaced with structured, evidence-based task instructions |
| 2 | All task `expected_output` | Required fabricated URLs, contradictory strategies, made-up institutions | Replaced with professional structured output templates |
| 3 | `analyze_financial_document` task | No `context` linking — tasks ran independently without prior verification | Added `context=[verification]` to chain tasks correctly |
| 4 | `investment_analysis` task | No `context` linking to analysis task | Added `context=[analyze_financial_document]` |
| 5 | `risk_assessment` task | No `context` linking to analysis task | Added `context=[analyze_financial_document]` |
| 6 | Agent assignments | Multiple tasks incorrectly all assigned to `financial_analyst` | `investment_analysis` → `investment_advisor`, `risk_assessment` → `risk_assessor`, `verification` → `verifier` |
| 7 | `verification` task | Told agent to "hallucinate financial terms" | Professional document verification task |
| 8 | Task descriptions | Encouraged non-compliance and regulatory violations | All tasks now include regulatory compliance guidance |

### `tools.py` — 4 Bugs

| # | Location | Bug | Fix |
|---|----------|-----|-----|
| 1 | Import | `from crewai_tools import tools` — imports the module, not a class | `from crewai_tools import SerperDevTool` |
| 2 | Import | `from crewai_tools.tools.serper_dev_tool import SerperDevTool` — wrong path | Simplified to correct import |
| 3 | `read_data_tool` | `async def` — crewai tools must be synchronous | Changed to `@staticmethod def` |
| 4 | `read_data_tool` | `Pdf(file_path=path).load()` — `Pdf` is undefined | `PyPDFLoader(file_path=path).load()` from `langchain_community.document_loaders` |

### `main.py` — 4 Bugs

| # | Location | Bug | Fix |
|---|----------|-----|-----|
| 1 | Import | `from task import analyze_financial_document` — conflicts with FastAPI endpoint function name of same name, causing NameError | Import aliased as `doc_analysis_task` |
| 2 | `run_crew` | Only included `financial_analyst` in agents and tasks — other agents/tasks never ran | All 4 agents and all 4 tasks included |
| 3 | Query validation | `if query=="" or query is None` — None check after `==` risks AttributeError | `if not query or not query.strip()` |
| 4 | `uvicorn.run` | `reload=True` in `__main__` block causes reload loops | `reload=False` for direct execution |

### `requirements.txt` — 3 Bugs

| # | Bug | Fix |
|---|-----|-----|
| 1 | Missing `python-multipart` — required for FastAPI `File`/`Form` uploads | Added `python-multipart==0.0.9` |
| 2 | Missing `uvicorn` — required to run the FastAPI app | Added `uvicorn[standard]` |
| 3 | Missing `pypdf` and `langchain-community` — required for PDF reading | Added both packages |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
│  POST /analyze        →  Synchronous     │
│  POST /analyze/async  →  Enqueues job → returns job_id      │
│  GET  /jobs/{id}      →  Poll job status + result           │
│  GET  /jobs           →  List all jobs (paginated)          │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
         Synchronous              Celery Queue
               │                   (Redis)
               │                        │
               └──────────┬─────────────┘
                           │
                    CrewAI Crew
                    ┌──────┴──────┐
               Sequential Process
                    │
          ┌─────────▼──────────┐
          │  1. Verifier Agent │  ← Validates document type
          └─────────┬──────────┘
          ┌─────────▼──────────┐
          │  2. Financial      │  ← Extracts metrics & trends
          │     Analyst Agent  │
          └─────────┬──────────┘
          ┌─────────▼──────────┐
          │  3. Investment     │  ← Bull/bear case analysis
          │     Advisor Agent  │
          └─────────┬──────────┘
          ┌─────────▼──────────┐
          │  4. Risk Assessor  │  ← Risk matrix & assessment
          └─────────┬──────────┘
                    │
             SQLite / PostgreSQL
             (AnalysisJob table)
```

---

## Setup & Installation

### 1. Clone / Extract the project

```bash
cd financial-document-analyzer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env .env
# Edit .env and add your API keys:
```

#### Required keys:
- `GEMINI_API_KEY` — from [aistudio.google.com]( https://aistudio.google.com/apikey)
##### * optional *
- `OPENAI_API_KEY` — from [platform.openai.com](https://platform.openai.com)
- `SERPER_API_KEY` — from [serper.dev](https://serper.dev)

### 5. Add a sample financial document

```bash
# Download Tesla Q2 2025 report (or use any financial PDF)
curl -o data/sample.pdf "https://www.tesla.com/sites/default/files/downloads/TSLA-Q2-2025-Update.pdf"
```

### 6. Run the API server

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
or

```bash
python main.py
```

The API will be available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## Bonus Features

### Queue Worker (Redis + Celery)

Handles concurrent analysis requests without blocking the API.

#### Start Redis (Docker — easiest)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

#### Start the Celery worker

```bash
celery -A worker worker --loglevel=info --concurrency=4
```

Now use `/analyze/async` to submit jobs and `/jobs/{job_id}` to poll results.

### Database Integration (SQLAlchemy)

All analysis jobs are automatically persisted.

**Default**: SQLite (`financial_analyzer.db`) — zero configuration needed.

**PostgreSQL** (production-ready):
```bash
# In .env:
DATABASE_URL=postgresql://user:password@localhost:5432/financial_analyzer
```

---

## API Documentation

### `GET /`
Health check.

**Response:**
```json
{
  "message": "Financial Document Analyzer API is running",
  "version": "2.0.0"
}
```

---

### `POST /analyze`
Upload and analyze a financial PDF synchronously.

**Request:** `multipart/form-data`
- `file` (required): PDF file
- `query` (optional): Analysis question (default: general investment analysis)

**Response:**
```json
{
  "status": "success",
  "job_id": "uuid",
  "query": "What are the key revenue drivers?",
  "analysis": "## Executive Summary\n...",
  "file_processed": "TSLA-Q2-2025.pdf"
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@data/TSLA-Q2-2025-Update.pdf" \
  -F "query=What are Tesla's main revenue drivers and risks?"
```

---

### `POST /analyze/async` *(Bonus)*
Submit a document for async analysis via Celery queue. Returns immediately.

**Request:** Same as `/analyze`

**Response:**
```json
{
  "status": "queued",
  "job_id": "uuid",
  "message": "Analysis queued. Poll /jobs/{job_id} for results.",
  "poll_url": "/jobs/uuid"
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/analyze/async \
  -F "file=@data/TSLA-Q2-2025-Update.pdf" \
  -F "query=Analyze investment risks"
```

---

### `GET /jobs/{job_id}` *(Bonus)*
Get the status and result of an analysis job.

**Response:**
```json
{
  "job_id": "uuid",
  "filename": "TSLA-Q2-2025.pdf",
  "query": "Analyze investment risks",
  "status": "completed",
  "analysis": "## Risk Assessment\n...",
  "created_at": "2025-02-25T10:00:00",
  "completed_at": "2025-02-25T10:02:30"
}
```

Status values: `pending` | `processing` | `completed` | `failed`

---

### `GET /jobs` *(Bonus)*
List all analysis jobs with pagination.

---

### `GET /docs` 
 it's an automatic interactive API documentation page that FastAPI generates,


**Query params:**
- `limit` (int, default: 20)
- `offset` (int, default: 0)

**Example:**
```bash
curl "http://localhost:8000/jobs?limit=10&offset=0"
```

---

### `DELETE /jobs/{job_id}` *(Bonus)*
Delete a job record from the database.

---

## Project Structure

```
financial-document-analyzer/
├── main.py              # FastAPI app — sync + async endpoints
├── agents.py            # CrewAI agent definitions (fixed)
├── task.py              # CrewAI task definitions (fixed)
├── tools.py             # PDF reader + search tools (fixed)
├── database.py          # SQLAlchemy models (bonus)
├── worker.py            # Celery worker (bonus)
├── requirements.txt     # Python dependencies (fixed)
├── .env.example         # Environment variable template
├── data/                # PDF uploads (auto-created, gitignored)
└── outputs/             # Analysis outputs
```

---

## Disclaimer

This tool provides AI-generated financial analysis for informational purposes only. It is **not** personalized financial advice. Always consult a licensed financial advisor before making investment decisions. Past performance does not guarantee future results.
