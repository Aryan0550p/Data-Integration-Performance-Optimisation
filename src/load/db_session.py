"""
Database Engine, Session Management, and Table Initialization
"""
from typing import Generator
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from config.settings import get_database_url, DB_TYPE, SQL_DIR, SCHEMA_DIR
from src.load.models import Base
from src.utils.logger import logger

# Create engine
db_url = get_database_url()
engine_args = {"echo": False, "future": True}

if db_url.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(db_url, **engine_args)

# Enable foreign keys for SQLite
if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(use_ddl_file: bool = True) -> None:
    """Initialize database tables using DDL file or SQLAlchemy metadata."""
    logger.info(f"Initializing database using engine: {engine.url}")
    if use_ddl_file:
        ddl_file = SCHEMA_DIR / ("01_create_tables.sql" if DB_TYPE == "postgresql" else "02_create_tables_sqlite.sql")
        if ddl_file.exists():
            with open(ddl_file, "r", encoding="utf-8") as f:
                sql_script = f.read()
            with engine.connect() as conn:
                for statement in sql_script.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        conn.execute(text(stmt))
                conn.commit()
            logger.info(f"Database schema initialized from DDL script: {ddl_file.name}")
            return

    # Fallback to SQLAlchemy metadata
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized from SQLAlchemy Base.metadata.")

def reset_db() -> None:
    """Drop and recreate all database tables."""
    logger.info("Resetting all database tables...")
    init_db(use_ddl_file=True)
