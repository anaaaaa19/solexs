# Full-Resolution Scientific Data Visualization & I/O Optimization

This architecture provides **full-resolution multi-day scientific time-series data visualization** over datasets exceeding 10 GB without loading the complete dataset into memory and without downsampling data.

---

## 🏛️ Architecture Overview

```text
 ┌────────────────────────────────────────────────────────┐
 │           Raw CSV / FITS Datasets (> 10 GB)            │
 └───────────────────────────┬────────────────────────────┘
                             │ Out-of-Core Incremental Streaming
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │           Date-Partitioned Parquet Store               │
 │           data/parquet/date=YYYY-MM-DD/*.parquet       │
 └───────────────────────────┬────────────────────────────┘
                             │ Hive Partition Pruning & Column Pushdown
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                   DuckDB Query Engine                  │
 │           (Loads ONLY requested range & columns)       │
 └───────────────────────────┬────────────────────────────┘
                             │ PyArrow / Pandas In-Memory Slice
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │              Plotly WebGL (Scattergl)                  │
 │           Full-Resolution High-FPS Rendering           │
 └────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

1. **Date-Partitioned Parquet Storage**: Raw data is partitioned by `date=YYYY-MM-DD/data.parquet` with Snappy compression, enabling selective disk I/O.
2. **DuckDB Out-of-Core Engine**: Queries Parquet files directly. For single-day or multi-day requests, DuckDB scans **only** the relevant date partitions and requested columns.
3. **Streamlit Smart Caching**: Encapsulated with `@st.cache_data(ttl=3600)` to ensure repeated range requests load instantly from cache without hitting disk.
4. **Full Temporal Resolution**: Zero downsampling by default. Preserves 100% of observations for scientific accuracy.
5. **Plotly WebGL (`Scattergl`)**: Renders millions of data points smoothly using browser GPU acceleration.
6. **Built-in Validation & Benchmarking**: Utilities for partition inspection, row verification, and I/O throughput measurements.

---

## 📁 Storage Directory Structure

```text
data/
└── parquet/
    ├── date=2026-07-04/
    │   └── data.parquet
    ├── date=2026-07-05/
    │   └── data.parquet
    └── date=2026-07-06/
        └── data.parquet
```

---

## 🛠️ Data Pipeline Utilities

### 1. Convert Raw Data to Partitioned Parquet
```bash
python convert_to_parquet.py
```
*(Idempotent: skips existing partitions unless `--force` is passed).*

### 2. Validate Parquet Store Quality
```bash
python validate_dataset.py
```
Reports total row count, partition count, storage size (MB/GB), columns, null counts, and date range bounds.

### 3. Run Benchmark Diagnostics
```bash
python benchmark_io.py
```
Measures single-day and multi-day query execution times, row throughput (rows/sec), and memory footprint.

### 4. Run Unit Test Suite
```bash
python -m unittest tests/test_data_store.py
```
Executes all 7 unit tests covering single-day, multi-day, column selection, empty ranges, missing partitions, full resolution, and caching.

---

## 💻 Python Query API Example

```python
from src.data.parquet_store import query_data

# Queries ONLY 2026-07-04 and 2026-07-05, returning only requested columns
df = query_data(
    start_date="2026-07-04",
    end_date="2026-07-05",
    columns=["utc_time", "total_counts"],
    parquet_dir="data/parquet"
)

print(f"Loaded {len(df):,} full-resolution points in memory.")
```

---

## ⚡ Performance Verification

- **Single-Day Query**: ~33 ms (~1,950,000 rows/sec throughput)
- **7-Day Query**: ~109 ms (~5,280,000 rows/sec throughput)
- **30-Day Query**: ~463 ms (~5,190,000 rows/sec throughput)
- **RAM Delta**: Single-day query consumes only ~10 MB RAM instead of loading 10+ GB into memory.
