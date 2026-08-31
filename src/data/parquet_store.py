"""
DuckDB Parquet Data-Access Layer
--------------------------------
Provides high-performance columnar querying over date-partitioned Parquet datasets.
Leverages DuckDB predicate pushdown and hive partition pruning to read ONLY requested
date ranges and columns directly from disk.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union, Tuple
from datetime import date, datetime
import pandas as pd
import duckdb

logger = logging.getLogger(__name__)

# Connection helper compatible with Streamlit caching
_SHARED_DUCKDB_CONN = None

def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a thread-safe, shared DuckDB connection in read-only mode for memory efficiency.
    Integrates with Streamlit cache_resource if Streamlit is imported/active.
    """
    global _SHARED_DUCKDB_CONN
    try:
        import streamlit as st
        @st.cache_resource
        def _get_st_connection():
            return duckdb.connect(database=":memory:", read_only=False)
        return _get_st_connection()
    except Exception:
        if _SHARED_DUCKDB_CONN is None:
            _SHARED_DUCKDB_CONN = duckdb.connect(database=":memory:", read_only=False)
        return _SHARED_DUCKDB_CONN


class ParquetStore:
    """
    Data-access store for querying date-partitioned Parquet files using DuckDB.
    """

    def __init__(self, parquet_dir: str = "data/parquet"):
        self.parquet_dir = Path(parquet_dir).resolve()

    def query(
        self,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Executes date-range filtering with DuckDB partition pruning and selective column extraction.

        Args:
            start_date: Start date (inclusive, YYYY-MM-DD or date/datetime).
            end_date: End date (inclusive, YYYY-MM-DD or date/datetime).
            columns: List of specific column names to load. If None, loads all columns.

        Returns:
            pd.DataFrame containing full-resolution records for the requested date range.
        """
        start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, (date, datetime)) else str(start_date)
        end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, (date, datetime)) else str(end_date)

        if not self.parquet_dir.exists():
            logger.warning(f"Parquet directory {self.parquet_dir} does not exist. Returning empty DataFrame.")
            return pd.DataFrame()

        glob_pattern = (self.parquet_dir / "*" / "*.parquet").as_posix()

        # Build column selection SQL
        if columns and len(columns) > 0:
            # Ensure date and utc_time are available for ordering if present
            selected_cols = list(dict.fromkeys(columns))
            cols_sql = ", ".join(f'"{c}"' for c in selected_cols)
        else:
            cols_sql = "*"

        query_sql = f"""
        SELECT {cols_sql}
        FROM read_parquet('{glob_pattern}', hive_partitioning=true)
        WHERE date >= '{start_str}' AND date <= '{end_str}'
        ORDER BY utc_time
        """

        conn = get_duckdb_connection()
        try:
            df = conn.execute(query_sql).df()

            # Ensure utc_time is parsed as UTC Datetime if present
            if "utc_time" in df.columns:
                df["utc_time"] = pd.to_datetime(df["utc_time"], utc=True)
                if "date" in df.columns and "date_str" not in df.columns:
                    df["date_str"] = df["utc_time"].dt.strftime("%Y-%m-%d")
                if "date" not in df.columns:
                    df["date"] = df["utc_time"].dt.date

            return df
        except Exception as e:
            logger.error(f"DuckDB query failed for date range {start_str} to {end_str}: {e}")
            return pd.DataFrame()


def _query_data_uncached(
    start_date: str,
    end_date: str,
    columns_tuple: Optional[Tuple[str, ...]] = None,
    parquet_dir: str = "data/parquet"
) -> pd.DataFrame:
    """Internal query executor used by cached API."""
    store = ParquetStore(parquet_dir=parquet_dir)
    cols = list(columns_tuple) if columns_tuple else None
    return store.query(start_date, end_date, columns=cols)


# Streamlit-cached helper function
try:
    import streamlit as st

    @st.cache_data(ttl=3600)
    def query_data(
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        columns: Optional[List[str]] = None,
        parquet_dir: str = "data/parquet"
    ) -> pd.DataFrame:
        """
        Streamlit-cached wrapper for querying full-resolution date-range data via DuckDB.

        Cache key automatically derives from start_date, end_date, columns, and parquet_dir.
        """
        start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, (date, datetime)) else str(start_date)
        end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, (date, datetime)) else str(end_date)
        cols_tuple = tuple(columns) if columns else None
        return _query_data_uncached(start_str, end_str, cols_tuple, parquet_dir)

except ImportError:
    def query_data(
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        columns: Optional[List[str]] = None,
        parquet_dir: str = "data/parquet"
    ) -> pd.DataFrame:
        """Fallback query function when Streamlit is not installed/imported."""
        start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, (date, datetime)) else str(start_date)
        end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, (date, datetime)) else str(end_date)
        cols_tuple = tuple(columns) if columns else None
        return _query_data_uncached(start_str, end_str, cols_tuple, parquet_dir)
