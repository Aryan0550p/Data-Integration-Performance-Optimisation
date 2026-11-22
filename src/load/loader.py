"""
High-Performance Bulk Loader into Unified Relational Database (8 Tables)
"""
import time
from typing import Dict
import pandas as pd
from sqlalchemy import text
from src.load.db_session import engine
from src.utils.logger import logger

TABLE_LOAD_ORDER = [
    "dim_customers",
    "dim_products",
    "dim_warehouses",
    "dim_campaigns",
    "dim_date",
    "fact_orders",
    "fact_order_items",
    "fact_shipments"
]

class DatabaseLoader:
    """Loads transformed DataFrames into PostgreSQL / SQLite database."""

    def __init__(self, db_engine=engine):
        self.engine = db_engine

    def load_table(self, table_name: str, df: pd.DataFrame, chunksize: int = 1000) -> int:
        """Bulk load DataFrame into database table using fast chunking."""
        start_time = time.time()
        logger.info(f"Loading {len(df):,} records into '{table_name}'...")
        is_sqlite = str(self.engine.url).startswith("sqlite")
        effective_chunk = 60 if is_sqlite else chunksize

        with self.engine.begin() as conn:
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists="append",
                index=False,
                chunksize=effective_chunk,
                method=None
            )
        elapsed = time.time() - start_time
        logger.info(f"Successfully loaded '{table_name}': {len(df):,} rows in {elapsed:.2f}s ({len(df)/max(elapsed, 0.001):.0f} rows/s)")
        return len(df)

    def load_all(self, tables_dict: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """Load all 8 tables in correct dependency order."""
        load_summary = {}
        for table_name in TABLE_LOAD_ORDER:
            if table_name in tables_dict:
                df = tables_dict[table_name]
                rows_loaded = self.load_table(table_name, df)
                load_summary[table_name] = rows_loaded
            else:
                logger.warning(f"Table '{table_name}' not found in provided dictionary.")
        return load_summary

    def get_table_counts(self) -> Dict[str, int]:
        """Fetch row counts from all 8 tables in the warehouse."""
        counts = {}
        with self.engine.connect() as conn:
            for tbl in TABLE_LOAD_ORDER:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                counts[tbl] = res
        return counts
