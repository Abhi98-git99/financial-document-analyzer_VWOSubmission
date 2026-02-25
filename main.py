from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import datetime

from fastapi.responses import HTMLResponse

from crewai import Crew, Process
# FIX: agents imported correctly — financial_analyst is defined in agents.py
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
# FIX: task module imported correctly; tasks are imported individually
from task import (
    analyze_financial_document as doc_analysis_task,
    verification,
    investment_analysis,
    risk_assessment,
)

# Bonus: Database and Queue imports
from database import SessionLocal, AnalysisJob, init_db
from worker import celery_app, run_crew_task

app = FastAPI(
    title="Financial Document Analyzer",
    description="AI-powered financial document analysis with investment insights and risk assessment",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FIX: run_crew used 'analyze_financial_document' as both the import alias AND the FastAPI endpoint
#      function name, causing a NameError. Renamed import alias to doc_analysis_task above.
def run_crew(query: str, file_path: str = "data/sample.pdf") -> str:
    """Run the full multi-agent crew synchronously."""
    query_with_path = f"{query}\n\nDocument file path: {file_path}"


    financial_crew = Crew(
        # FIX: agents list now includes all relevant agents (was missing verifier, advisor, assessor)
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        # FIX: tasks list now includes all four tasks in correct sequential order
        tasks=[verification, doc_analysis_task, investment_analysis, risk_assessment],
        process=Process.sequential,
        verbose=True,
    )
    result = financial_crew.kickoff({"query": query_with_path})
    return str(result)


# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "message": "Financial Document Analyzer API is running",
#         "version": "2.0.0",
#         "endpoints": ["/analyze", "/analyze/async", "/jobs/{job_id}", "/jobs"],
#     }

@app.get("/")
async def root():
    """Health check with popup then redirect to /jobs"""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Financial Document Analyzer</title>
        </head>
        <body>
            <script>
                alert("✅ 200 OK — Financial Document Analyzer API is running!");
                window.location.href = "/docs";
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ── SYNCHRONOUS ENDPOINT ─────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_document_sync(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
):
    """
    Upload a financial document and receive an analysis synchronously in the response.
    """
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # FIX: was 'if query == "" or query is None' — None check must come first to avoid
        #      AttributeError when query is None (short-circuit doesn't help with ==)
        if not query or not query.strip():
            query = "Analyze this financial document for investment insights"

        result = run_crew(query=query.strip(), file_path=file_path)

        # Store result in DB
        job = AnalysisJob(
            id=file_id,
            filename=file.filename,
            query=query.strip(),
            status="completed",
            result=result,
            created_at=datetime.datetime.utcnow(),
            completed_at=datetime.datetime.utcnow(),
        )
        db.add(job)
        db.commit()

        return {
            "status": "success",
            "job_id": file_id,
            "query": query,
            "analysis": result,
            "file_processed": file.filename,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing financial document: {str(e)}"
        )

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

# Bonus 1
# ── ASYNC / QUEUE ENDPOINT (Bonus: Celery + Redis) ────────────────────────────

@app.post("/analyze/async")
async def analyze_document_async(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
):
    """
    Submit a financial document for asynchronous analysis via Celery queue.
    Returns a job_id immediately; poll /jobs/{job_id} for results.
    """
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    os.makedirs("data", exist_ok=True)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if not query or not query.strip():
        query = "Analyze this financial document for investment insights"

    # Store pending job in DB
    job = AnalysisJob(
        id=file_id,
        filename=file.filename,
        query=query.strip(),
        status="pending",
        result=None,
        created_at=datetime.datetime.utcnow(),
        completed_at=None,
    )
    db.add(job)
    db.commit()

    # Dispatch to Celery worker
    run_crew_task.apply_async(
        args=[file_id, query.strip(), file_path],
        task_id=file_id,
    )

    return {
        "status": "queued",
        "job_id": file_id,
        "message": "Analysis queued. Poll /jobs/{job_id} for results.",
        "poll_url": f"/jobs/{file_id}",
    }

# Bonus 2
# ── JOB STATUS ENDPOINTS (Bonus: Database Integration) ────────────────────────

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Retrieve the status and result of an analysis job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": job.id,
        "filename": job.filename,
        "query": job.query,
        "status": job.status,
        "analysis": job.result,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@app.get("/jobs")
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all analysis jobs with pagination."""
    jobs = (
        db.query(AnalysisJob)
        .order_by(AnalysisJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(AnalysisJob).count()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "job_id": j.id,
                "filename": j.filename,
                "query": j.query,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ],
    }


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete an analysis job record."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    # FIX: reload=True causes issues when run as __main__; set to False for direct execution
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
