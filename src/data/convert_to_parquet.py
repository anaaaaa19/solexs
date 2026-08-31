"""
CSV / Raw Data -> Date-Partitioned Parquet Converter
-----------------------------------------------------
Converts raw CSV/FITS/Parquet time-series datasets into date-partitioned Parquet files
using DuckDB streaming. Ensures full resolution is preserved without loading the entire
dataset into memory at once.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def convert_raw_to_parquet(
    source_path: str,
    output_dir: str = "data/parquet",
    date_column: str = "utc_time",
    compression: str = "SNAPPY",
    force: bool = False
) -> Dict[str, Any]:
    """
    Incrementally converts source CSV / Parquet file into date-partitioned Parquet directory structure.

    Args:
        source_path: Absolute or relative path to source CSV or Parquet file.
        output_dir: Target output directory for Hive-style partitions (default: 'data/parquet').
        date_column: Timestamp column name to derive date partition key from (default: 'utc_time').
        compression: Compression codec for Parquet files (default: 'SNAPPY').
        force: If True, rebuilds partitions even if target directory already exists.

    Returns:
        Dict containing conversion metadata: rows_converted, partition_count, duration_seconds, output_dir.
    """
    start_time = time.time()
    source_p = Path(source_path)
    output_p = Path(output_dir)

    if not source_p.exists():
        raise FileNotFoundError(f"Source data file not found: {source_path}")

    output_p.mkdir(parents=True, exist_ok=True)

    # Check idempotency: If partitions already exist and not force, skip rebuilding
    existing_partitions = list(output_p.glob("date=*"))
    if existing_partitions and not force:
        logger.info(
            f"Partitioned Parquet store already exists at {output_dir} "
            f"({len(existing_partitions)} partitions found). Skipping conversion (use force=True to rebuild)."
        )
        conn = duckdb.connect()
        try:
            total_rows = conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{output_p.as_posix()}/*/*.parquet', hive_partitioning=true)"
            ).fetchone()[0]
        except Exception:
            total_rows = -1
        finally:
            conn.close()

        return {
            "status": "skipped",
            "reason": "already_exists",
            "output_dir": str(output_p),
            "partition_count": len(existing_partitions),
            "total_rows": total_rows,
            "duration_seconds": round(time.time() - start_time, 3)
        }

    logger.info(f"Starting conversion of {source_path} to partitioned Parquet store at {output_dir}...")

    conn = duckdb.connect()
    try:
        # Determine source file format (CSV vs Parquet)
        if source_p.suffix.lower() == ".csv":
            read_sql = f"read_csv_auto('{source_p.as_posix()}')"
        elif source_p.suffix.lower() in [".parquet", ".pq"]:
            read_sql = f"read_parquet('{source_p.as_posix()}')"
        else:
            raise ValueError(f"Unsupported file format: {source_p.suffix}. Supported: .csv, .parquet")

        # Construct DuckDB streaming COPY command with Hive-style partition pruning
        copy_sql = f"""
        COPY (
            SELECT 
                *,
                strftime(CAST({date_column} AS TIMESTAMP), '%Y-%m-%d') AS date
            FROM {read_sql}
            WHERE {date_column} IS NOT NULL
        )
        TO '{output_p.as_posix()}'
        (FORMAT PARQUET, PARTITION_BY (date), COMPRESSION '{compression}');
        """

        logger.info("Executing DuckDB out-of-core partitioned export...")
        conn.execute(copy_sql)

        # Count total rows and partitions created
        partitions = list(output_p.glob("date=*"))
        total_rows = conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{output_p.as_posix()}/*/*.parquet', hive_partitioning=true)"
        ).fetchone()[0]

        duration = round(time.time() - start_time, 3)
        logger.info(
            f"Successfully converted {total_rows:,} records into {len(partitions)} date partitions "
            f"in {duration} seconds."
        )

        return {
            "status": "success",
            "output_dir": str(output_p),
            "partition_count": len(partitions),
            "total_rows": total_rows,
            "duration_seconds": duration,
            "compression": compression
        }

    finally:
        conn.close()


if __name__ == "__main__":
    # Command-line entry point
    root_dir = Path(__file__).resolve().parents[2] if len(sys.argv) < 2 else Path(sys.argv[1])
    master_parquet = root_dir / "solexs_master_timeseries.parquet"
    target_parquet_dir = root_dir / "data" / "parquet"

    if master_parquet.exists():
        res = convert_raw_to_parquet(
            source_path=str(master_parquet),
            output_dir=str(target_parquet_dir),
            date_column="utc_time",
            force=False
        )
        print("Conversion result:", res)
    else:
        print(f"Master file {master_parquet} not found. Please specify source path.")
