# SoLEXS Solar Flare Analysis & Forecasting Dashboard

An interactive **Streamlit** web application for exploring observations from the **Solar Low Energy X-ray Spectrometer (SoLEXS SDD2)** instrument aboard ISRO's Aditya-L1 solar mission.

---

## Prerequisite Pipeline Execution Order

Before launching the dashboard, ensure the data processing and machine learning pipelines have executed to generate all required input artifacts:

```bash
# Step 1: Extract nested archives
python extract_archives.py

# Step 2: Batch load SDD2 FITS files into parquet & npy master datasets
python batch_load.py

# Step 2b: Convert raw master dataset to Hive-partitioned Parquet store
python convert_to_parquet.py

# Step 2c: Validate partitioned dataset & check storage stats
python validate_dataset.py

# Step 2d: Run I/O and memory benchmark diagnostic
python benchmark_io.py

# Step 3, 4, 5, 6, 7: Gap analysis, MAD flare detection & diagnostic plots
python gap_check_and_visualize.py

# Step 8: Empirical GOES flux calibration against NOAA events
python calibration.py

# Step 9: Gap-aware feature engineering & 15m forecast labeling
python feature_engineering.py

# Step 10: Train XGBoost classifier, evaluate test set & export model JSON/metadata
python train_model.py
```

---

## How to Run the Dashboard

Install dependencies:
```bash
pip install -r requirements.txt
```

Launch the Streamlit web application:
```bash
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## Dashboard Architecture & Navigation

The dashboard features a global date-range selector in the sidebar that filters all views dynamically, organized into 9 dedicated sections:

1. **Overview**: Key metrics, coverage stats, and high-level date breakdown.
2. **Light Curve**: Interactive Plotly light curve (`total_counts` vs `utc_time`) with background line, flare candidate scatter points, and `excess` toggles.
3. **Per-Day Grid**: 5-column small multiples grid of per-day light curves.
4. **Flare Event Explorer**: Sortable catalog table, $\pm 10\text{m}$ zoomed light curve, 340-channel peak vs quiet spectrum comparison, empirical GOES flux ($\text{W/m}^2$) and GOES class with mandatory calibration caveats.
5. **Energy Spectrogram**: Time-vs-channel count intensity heatmap across 340 channels ($0-339$).
6. **Daily Summary**: Daily Peak Activity bar chart, daily statistics table with visual low-coverage indicators ($N < 75,000$).
7. **Data Quality / Gaps**: Timeline breakdown of gaps $> 60\text{s}$, missing dates, and classification of clean missing dates vs dense telemetry dropouts.
8. **Predictive Analysis**: XGBoost model metadata, feature importance rankings, predicted 15-minute flare risk probability timeline, false alarm table, and missed event table.
9. **Ground-Truth Cross-Check**: Cross-match table of SoLEXS events against matched NOAA/GOES solar flares.
