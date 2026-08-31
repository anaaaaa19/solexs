"""
Unit Tests for Data Store & Query Layer
---------------------------------------
Tests single-day, multi-day, column selection, empty ranges, missing partitions,
full resolution preservation, and caching capabilities.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.parquet_store import ParquetStore, query_data
from src.data.validate_dataset import validate_parquet_store


class TestDataStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parquet_dir = str(PROJECT_ROOT / "data" / "parquet")
        cls.store = ParquetStore(parquet_dir=cls.parquet_dir)

    def test_1_single_day_query(self):
        """Test 1 — Single day: Verify only requested date is returned."""
        df = self.store.query("2026-07-04", "2026-07-04")
        self.assertFalse(df.empty, "DataFrame should not be empty for 2026-07-04")
        unique_dates = df["date_str"].unique()
        self.assertEqual(len(unique_dates), 1)
        self.assertEqual(unique_dates[0], "2026-07-04")

    def test_2_multi_day_query(self):
        """Test 2 — Multi-day range: Verify all requested days are returned and no unrelated dates."""
        df = self.store.query("2026-07-04", "2026-07-06")
        self.assertFalse(df.empty, "DataFrame should not be empty for 2026-07-04 to 2026-07-06")
        unique_dates = sorted(df["date_str"].unique().tolist())
        self.assertEqual(unique_dates, ["2026-07-04", "2026-07-05", "2026-07-06"])

    def test_3_column_selection(self):
        """Test 3 — Column selection: Verify only requested columns are loaded."""
        requested_cols = ["utc_time", "total_counts"]
        df = self.store.query("2026-07-04", "2026-07-04", columns=requested_cols)
        self.assertFalse(df.empty)
        # Check that requested columns are present and unrequested columns (e.g. TSTART, EXPOSURE) are not
        self.assertIn("utc_time", df.columns)
        self.assertIn("total_counts", df.columns)
        self.assertNotIn("EXPOSURE", df.columns)

    def test_4_empty_range(self):
        """Test 4 — Empty range: Verify an empty result is handled cleanly."""
        df = self.store.query("2025-01-01", "2025-01-02")
        self.assertTrue(df.empty, "Query for non-existent date range should return an empty DataFrame")

    def test_5_missing_partition(self):
        """Test 5 — Missing partition: Verify missing dates do not crash the application."""
        # Query date range that spans missing dates (e.g. 2026-08-11 to 2026-08-12)
        df = self.store.query("2026-08-10", "2026-08-13")
        # Should return valid data for available partitions (08-10, 08-13) without crashing
        self.assertFalse(df.empty)

    def test_6_full_resolution(self):
        """Test 6 — Full resolution: Verify that returned records match exact source records (no hidden downsampling)."""
        df_single = self.store.query("2026-07-04", "2026-07-04")
        val_report = validate_parquet_store(self.parquet_dir)
        expected_rows_for_day = val_report.get("rows_per_partition", {}).get("2026-07-04")
        self.assertEqual(len(df_single), expected_rows_for_day, "Full resolution record count must match partition count exactly")

    def test_7_caching(self):
        """Test 7 — Cache: Verify repeated identical requests work seamlessly."""
        df1 = query_data("2026-07-04", "2026-07-04", columns=["utc_time", "total_counts"], parquet_dir=self.parquet_dir)
        df2 = query_data("2026-07-04", "2026-07-04", columns=["utc_time", "total_counts"], parquet_dir=self.parquet_dir)
        self.assertEqual(len(df1), len(df2))
        self.assertTrue((df1["total_counts"].values == df2["total_counts"].values).all())


if __name__ == "__main__":
    unittest.main()
