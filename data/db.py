"""
Database Connection & Session Management
SQLAlchemy initialization with WAL mode for SQLite
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from config.settings import DATABASE_URL, DB_WAL_MODE
from data.models import Base

# Create engine with SQLite optimizations
if "sqlite" in DATABASE_URL.lower():
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Enable WAL mode for better concurrency
    if DB_WAL_MODE:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.close()
else:
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized successfully")

def drop_db():
    """Drop all tables (for testing/reset)"""
    Base.metadata.drop_all(bind=engine)
    print("✓ Database dropped")

if __name__ == "__main__":
    init_db()
