"""
database.py — SQLAlchemy database models and session management.
Bonus feature: persistent storage of all analysis jobs and results.
"""

import os
import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default to SQLite for easy local dev; switch to PostgreSQL via DATABASE_URL env var
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_analyzer.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AnalysisJob(Base):
    """Stores financial document analysis jobs and their results."""
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, index=True)          # UUID
    filename = Column(String(255), nullable=True)                   # Original uploaded filename
    query = Column(Text, nullable=False)                            # User's analysis query
    status = Column(String(20), default="pending")                  # pending | processing | completed | failed
    result = Column(Text, nullable=True)                            # Full analysis result text
    error = Column(Text, nullable=True)                             # Error message if failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AnalysisJob id={self.id} status={self.status}>"


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
