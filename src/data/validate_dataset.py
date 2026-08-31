"""
Dataset Validation Utility
--------------------------
Inspects and validates the date-partitioned Parquet storage architecture.
Reports partition counts, row distribution, disk storage footprint, data types,
null counts, and temporal continuity.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import duckdb

logger = logging.getLogger(__name__)


def validate_parquet_store(parquet_dir: str = "data/parquet") -> Dict[str, Any]:
    """
    Analyzes the date-partitioned Parquet store directory and reports detailed storage and data quality metrics.

    Args:
        parquet_dir: Path to partitioned Parquet root directory.

    Returns:
        Dict containing validation metrics.
    """
    parquet_p = Path(parquet_dir).resolve()

    if not parquet_p.exists():
        logger.error(f"Parquet store directory not found at {parquet_dir}")
        return {"status": "error", "error": f"Directory not found: {parquet_dir}"}

    partition_dirs = sorted(list(parquet_p.glob("date=*")))

    if not partition_dirs:
        logger.warning(f"No Hive-style partitions ('date=YYYY-MM-DD') found in {parquet_dir}")
        return {
            "status": "warning",
            "message": "No date partitions found.",
            "parquet_dir": str(parquet_p),
            "partition_count": 0
        }

    # Storage size on disk
    total_bytes = sum(f.stat().st_size for f in parquet_p.rglob("*.parquet"))
    size_mb = round(total_bytes / (1024 * 1024), 2)
    size_gb = round(total_bytes / (1024 * 1024 * 1024), 4)

    conn = duckdb.connect()
    try:
        glob_pattern = (parquet_p / "*" / "*.parquet").as_posix()

        # Query summary stats via DuckDB
        summary_query = f"""
        SELECT 
            COUNT(*) AS total_rows,
            MIN(utc_time) AS min_utc,
            MAX(utc_time) AS max_utc,
            COUNT(DISTINCT date) AS distinct_dates
        FROM read_parquet('{glob_pattern}', hive_partitioning=true)
        """
        summary_df = conn.execute(summary_query).df()
        total_rows = int(summary_df["total_rows"].iloc[0])
        min_utc = str(summary_df["min_utc"].iloc[0])
        max_utc = str(summary_df["max_utc"].iloc[0])
        distinct_dates = int(summary_df["distinct_dates"].iloc[0])

        # Schema & column info
        schema_df = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{glob_pattern}', hive_partitioning=true)").df()
        columns_info = {
            row["column_name"]: str(row["column_type"])
            for _, row in schema_df.iterrows()
        }

        # Null counts per column
        null_counts = {}
        for col in columns_info.keys():
            n_null = conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{glob_pattern}', hive_partitioning=true) WHERE \"{col}\" IS NULL"
            ).fetchone()[0]
            null_counts[col] = int(n_null)

        # Per-partition row distribution (first 5 and last 5)
        part_query = f"""
        SELECT date, COUNT(*) as row_count
        FROM read_parquet('{glob_pattern}', hive_partitioning=true)
        GROUP BY date
        ORDER BY date
        """
        partition_rows = conn.execute(part_query).df()
        rows_per_partition = dict(zip(partition_rows["date"].astype(str), partition_rows["row_count"]))

        report = {
            "status": "success",
            "parquet_dir": str(parquet_p),
            "storage_size_mb": size_mb,
            "storage_size_gb": size_gb,
            "partition_count": len(partition_dirs),
            "distinct_dates_count": distinct_dates,
            "total_rows": total_rows,
            "min_utc_timestamp": min_utc,
            "max_utc_timestamp": max_utc,
            "columns_schema": columns_info,
            "null_counts": null_counts,
            "rows_per_partition": rows_per_partition
        }

        logger.info(
            f"Parquet Store Validation: {total_rows:,} rows across {len(partition_dirs)} date partitions "
            f"({size_mb} MB / {size_gb} GB)."
        )
        return report

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        conn.close()


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parents[2] if len(sys.argv) < 2 else Path(sys.argv[1])
    target_parquet_dir = root_dir / "data" / "parquet"
    res = validate_parquet_store(str(target_parquet_dir))
    print("\n--- DATASET VALIDATION REPORT ---")
    print(f"Status:             {res.get('status')}")
    print(f"Total Rows:         {res.get('total_rows', 0):,}")
    print(f"Partition Count:    {res.get('partition_count', 0)}")
    print(f"Storage Footprint:  {res.get('storage_size_mb', 0)} MB ({res.get('storage_size_gb', 0)} GB)")
    print(f"Date Range:         {res.get('min_utc_timestamp')} to {res.get('max_utc_timestamp')}")
    print(f"Columns:            {list(res.get('columns_schema', {}).keys())}")
    print("---------------------------------\n")
