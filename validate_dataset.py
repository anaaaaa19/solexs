"""
Root CLI wrapper for Parquet Dataset Validation
"""

import sys
from pathlib import Path
from src.data.validate_dataset import validate_parquet_store

if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent
    target_dir = root_dir / "data" / "parquet"

    print(f"Validating Parquet Store at {target_dir}...")
    res = validate_parquet_store(str(target_dir))
    
    print("\n==========================================")
    print("      PARQUET DATASET VALIDATION REPORT   ")
    print("==========================================")
    print(f"Status:             {res.get('status')}")
    print(f"Total Rows:         {res.get('total_rows', 0):,}")
    print(f"Partition Count:    {res.get('partition_count', 0)}")
    print(f"Storage Footprint:  {res.get('storage_size_mb', 0)} MB ({res.get('storage_size_gb', 0)} GB)")
    print(f"Min Timestamp:      {res.get('min_utc_timestamp')}")
    print(f"Max Timestamp:      {res.get('max_utc_timestamp')}")
    print("\nColumns & Data Types:")
    for col, dtype in res.get('columns_schema', {}).items():
        print(f"  - {col:<15} ({dtype}) | Nulls: {res.get('null_counts', {}).get(col, 0)}")
    print("==========================================\n")
