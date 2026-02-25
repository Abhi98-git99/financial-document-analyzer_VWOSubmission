"""
worker.py — Celery worker for async financial document analysis.
Bonus feature: Redis-backed queue for handling concurrent analysis requests.

Start the worker with:
    celery -A worker worker --loglevel=info --concurrency=4
"""

import os
import datetime
from celery import Celery

# Redis broker (default: localhost:6379, configurable via REDIS_URL env var)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "financial_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry failed tasks up to 3 times with exponential backoff
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # One task at a time per worker process
)


@celery_app.task(
    bind=True,
    name="worker.run_crew_task",
    max_retries=3,
    default_retry_delay=30,
)
def run_crew_task(self, job_id: str, query: str, file_path: str):
    """
    Celery task: runs the full CrewAI financial analysis crew.
    Updates the database with status and result when complete.
    """
    # Import inside task to avoid circular imports and ensure fresh DB session
    from database import SessionLocal, AnalysisJob
    from crewai import Crew, Process
    from agents import financial_analyst, verifier, investment_advisor, risk_assessor
    from task import (
        analyze_financial_document as doc_analysis_task,
        verification,
        investment_analysis,
        risk_assessment,
    )

    db = SessionLocal()

    try:
        # Mark job as processing
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = "processing"
            db.commit()

        # Run the crew
        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[verification, doc_analysis_task, investment_analysis, risk_assessment],
            process=Process.sequential,
            verbose=True,
        )
        result = financial_crew.kickoff({"query": query})
        result_str = str(result)

        # Update job with result
        if job:
            job.status = "completed"
            job.result = result_str
            job.completed_at = datetime.datetime.utcnow()
            db.commit()

        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:
        # Update job as failed
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.completed_at = datetime.datetime.utcnow()
            db.commit()

        # Retry on transient errors
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)

    finally:
        db.close()
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
