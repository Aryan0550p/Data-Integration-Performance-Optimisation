"""
Global Configuration and Settings for Data Integration Platform
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
QUARANTINE_DATA_DIR = DATA_DIR / "quarantine"
DOCS_DIR = PROJECT_ROOT / "docs"

# SQL Directories
SQL_DIR = PROJECT_ROOT / "sql"
SCHEMA_DIR = SQL_DIR / "schema"
INDEXES_DIR = SQL_DIR / "indexes"
QUERIES_DIR = SQL_DIR / "queries"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # 'postgresql' or 'sqlite'
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "enterprise_dw")

SQLITE_DB_PATH = DATA_DIR / "enterprise_dw.db"

def get_database_url() -> str:
    """Return appropriate database connection URL."""
    if DB_TYPE == "postgresql":
        return f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    return f"sqlite:///{SQLITE_DB_PATH}"

# Ensure directories exist
for p in [RAW_DATA_DIR, STAGING_DATA_DIR, QUARANTINE_DATA_DIR, SCHEMA_DIR, INDEXES_DIR, QUERIES_DIR, BENCHMARKS_DIR, DOCS_DIR]:
    p.mkdir(parents=True, exist_ok=True)
