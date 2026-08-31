"""
Root CLI wrapper for CSV/Parquet -> Date-Partitioned Parquet Converter
"""

import sys
from pathlib import Path
from src.data.convert_to_parquet import convert_raw_to_parquet

if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent
    master_parquet = root_dir / "solexs_master_timeseries.parquet"
    target_dir = root_dir / "data" / "parquet"
    
    force_flag = "--force" in sys.argv or "-f" in sys.argv

    if not master_parquet.exists():
        print(f"Error: Master dataset {master_parquet} does not exist!")
        sys.exit(1)

    print(f"Converting dataset {master_parquet} -> {target_dir} (force={force_flag})...")
    result = convert_raw_to_parquet(
        source_path=str(master_parquet),
        output_dir=str(target_dir),
        date_column="utc_time",
        force=force_flag
    )
    print("Result:", result)
