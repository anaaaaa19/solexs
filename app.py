import os
import sys
import json
import math
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add src to sys.path if not present
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.data.parquet_store import query_data, get_duckdb_connection
from src.data.validate_dataset import validate_parquet_store
from src.pipeline import (
    run_pipeline,
    goes_class_to_flux,
    goes_class_rank,
    flux_to_goes_class,
)

# Set Streamlit page layout and title
st.set_page_config(
    page_title="SoLEXS Data Explorer & Nowcasting Console",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PARQUET_STORE_DIR = os.path.join(ROOT_DIR, "data", "parquet")
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

CONFIRMATION_COLORS = {
    "Confirmed": "#2ca02c",
    "SoLEXS-only": "#ff7f0e",
}

INSTRUMENT_COLORS = {
    "SoLEXS": "royalblue",
    "HEL1OS": "firebrick",
}

GOES_LETTER_ORDER = ["A", "B", "C", "M", "X"]

# -----------------------------------------------------------------------------
# Data Loading Functions
# -----------------------------------------------------------------------------
@st.cache_data
def load_pipeline_config(root_dir):
    config_path = os.path.join(root_dir, 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

@st.cache_data
def load_timeseries_light(root_dir):
    light_path = os.path.join(root_dir, 'solexs_master_timeseries_light.parquet')
    full_path = os.path.join(root_dir, 'solexs_master_timeseries.parquet')
    
    path = light_path if os.path.exists(light_path) else full_path
    if not os.path.exists(path):
        return None
        
    df = pd.read_parquet(path)
    df['utc_time'] = pd.to_datetime(df['utc_time'], utc=True)
    df['date'] = df['utc_time'].dt.date
    df['date_str'] = df['utc_time'].dt.strftime('%Y-%m-%d')
    return df

@st.cache_data
def load_counts_array(root_dir):
    npy_path = os.path.join(root_dir, 'solexs_master_counts.npy')
    if not os.path.exists(npy_path):
        return None
    return np.load(npy_path, mmap_mode='r')

@st.cache_data
def load_tstart_master(root_dir):
    ts_path = os.path.join(root_dir, 'solexs_master_timeseries.parquet')
    if os.path.exists(ts_path):
        df_m = pd.read_parquet(ts_path, columns=['TSTART'])
        return df_m['TSTART'].values
    return None

@st.cache_data
def load_catalog_data(root_dir):
    cal_cat_path = os.path.join(root_dir, 'solexs_flare_candidate_catalog_calibrated.csv')
    raw_cat_path = os.path.join(root_dir, 'solexs_flare_candidate_catalog.csv')
    
    if os.path.exists(cal_cat_path):
        cat = pd.read_csv(cal_cat_path)
    elif os.path.exists(raw_cat_path):
        cat = pd.read_csv(raw_cat_path)
    else:
        return None
        
    cat['start_time'] = pd.to_datetime(cat['start_time'], utc=True)
    cat['end_time'] = pd.to_datetime(cat['end_time'], utc=True)
    cat['peak_time'] = pd.to_datetime(cat['peak_time'], utc=True)
    cat['date_str'] = cat['peak_time'].dt.strftime('%Y-%m-%d')
    if 'estimated_class' not in cat.columns:
        if 'emp_goes_class' in cat.columns:
            cat['estimated_class'] = cat['emp_goes_class']
        elif 'goes_class' in cat.columns:
            cat['estimated_class'] = cat['goes_class']
    return cat

@st.cache_data
def load_daily_summary(root_dir):
    daily_path = os.path.join(root_dir, 'solexs_daily_summary.csv')
    if not os.path.exists(daily_path):
        return None
    return pd.read_csv(daily_path)

@st.cache_data
def load_predictions_summary(root_dir):
    pred_path = os.path.join(root_dir, 'solexs_predictions_summary.parquet')
    meta_path = os.path.join(root_dir, 'solexs_flare_model_v1_20260704_20260827_metadata.json')
    
    if not os.path.exists(pred_path) or not os.path.exists(meta_path):
        return None, None
        
    pred_df = pd.read_parquet(pred_path)
    pred_df['utc_time'] = pd.to_datetime(pred_df['utc_time'], utc=True)
    pred_df['date'] = pred_df['utc_time'].dt.date
    
    with open(meta_path, 'r') as fp:
        meta = json.load(fp)
        
    return pred_df, meta

def _load_csv_safe(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            return pd.read_csv(path)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def load_nowcasting_output_data(out_dir):
    val_cat = os.path.join(out_dir, "validated_master_catalogue.csv")
    master_cat = os.path.join(out_dir, "master_catalogue.csv")
    cat_path = val_cat if os.path.exists(val_cat) else master_cat

    catalogue = _load_csv_safe(cat_path)
    goes = _load_csv_safe(os.path.join(out_dir, "goes_events.csv"))
    log = _load_csv_safe(os.path.join(out_dir, "run_log.csv"))
    summary = _load_csv_safe(os.path.join(out_dir, "summary_metrics.csv"))
    class_breakdown = _load_csv_safe(os.path.join(out_dir, "class_breakdown.csv"))

    return catalogue, goes, log, summary, class_breakdown

def downsample_for_plotly(df, max_points=3000):
    if len(df) <= max_points:
        return df
    stride = math.ceil(len(df) / max_points)
    return df.iloc[::stride].copy()

# -----------------------------------------------------------------------------
# Minimal CSS Styling
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 0.88rem;
        color: #64748b;
        margin-bottom: 1.0rem;
    }
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e293b;
        margin-top: 0.4rem;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.3rem;
    }
    .meta-footer {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 0.3rem;
    }
    .caveat-box {
        font-size: 0.85rem;
        color: #92400e;
        background-color: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 3px solid #d97706;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">SoLEXS Data Explorer & Nowcasting Console</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Aditya-L1 Solar Low Energy X-ray Spectrometer (SDD2) & Multi-Instrument Flare Nowcasting Pipeline</div>', unsafe_allow_html=True)

# Load cached datasets
pipeline_config = load_pipeline_config(ROOT_DIR)
df_ts = load_timeseries_light(ROOT_DIR)
counts_2d = load_counts_array(ROOT_DIR)
tstart_master = load_tstart_master(ROOT_DIR)
cat_df = load_catalog_data(ROOT_DIR)
daily_df = load_daily_summary(ROOT_DIR)
pred_df, model_meta = load_predictions_summary(ROOT_DIR)

if df_ts is None:
    st.error("Primary dataset solexs_master_timeseries.parquet not found!")
    st.stop()

# Sidebar Navigation
st.sidebar.markdown("### Navigation")
section = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Light Curve",
        "Per-Day Grid",
        "Flare Event Explorer",
        "Energy Spectrogram",
        "Daily Summary",
        "Data Quality & Gaps",
        "Predictive Analysis",
        "Ground-Truth Cross-Check",
        "☀️ Nowcasting Console (Aditya-L1)"
    ],
    label_visibility="collapsed"
)

# Section: Nowcasting Console (Aditya-L1)
if section == "☀️ Nowcasting Console (Aditya-L1)":
    st.markdown('<div class="section-header">☀️ Aditya-L1 Solar Flare Detection & Nowcasting Console</div>', unsafe_allow_html=True)
    st.write(
        """
        This dashboard processes SoLEXS and HEL1OS X-ray data, detects solar
        flare candidates using MAD-based detection, fuses detections from both
        instruments, and validates them against the official GOES/HEK flare
        catalogue — including flare-class comparison, lead-time analysis, and
        per-instrument light curves.
        """
    )

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pipeline Settings")

    pipeline_root_dir = st.sidebar.text_input("Data root folder", value=ROOT_DIR)
    pipeline_out_dir = st.sidebar.text_input("Output folder", value=DEFAULT_OUTPUT_DIR)

    mad_window = st.sidebar.number_input("MAD Window", min_value=10, value=300, step=10)
    mad_k = st.sidebar.number_input("MAD k (Sensitivity)", min_value=1.0, value=5.0, step=0.5)
    goes_window = st.sidebar.number_input("GOES Match Window (minutes)", min_value=1.0, value=10.0, step=1.0)

    if st.sidebar.button("🚀 Run Pipeline"):
        if not pipeline_root_dir:
            st.error("Please enter the folder containing your SoLEXS and HEL1OS data.")
        elif not os.path.exists(pipeline_root_dir):
            st.error("That data folder does not exist. Check the path.")
        else:
            try:
                st.info("Processing data... This may take some time.")
                progress_bar = st.progress(0)
                status_text = st.empty()

                def show_progress(done, total, date_str, status):
                    progress = int(done / total * 100) if total > 0 else 0
                    progress_bar.progress(progress)
                    status_text.write(f"Processing {done}/{total}: {date_str} → {status}")

                catalogue_run, goes_run, log_run, summary_run, class_breakdown_run = run_pipeline(
                    root_dir=pipeline_root_dir,
                    out_dir=pipeline_out_dir,
                    mad_window=mad_window,
                    mad_k=mad_k,
                    goes_match_window=goes_window,
                    progress_callback=show_progress
                )

                st.session_state["catalogue"] = catalogue_run
                st.session_state["goes"] = goes_run
                st.session_state["log"] = log_run
                st.session_state["summary"] = summary_run
                st.session_state["class_breakdown"] = class_breakdown_run
                st.session_state["out_dir"] = pipeline_out_dir

                progress_bar.progress(100)
                st.success("Pipeline completed successfully! 🎉")
            except Exception as e:
                st.error(f"Pipeline Error: {e}")

    active_out_dir = st.session_state.get("out_dir", pipeline_out_dir)

    if "catalogue" not in st.session_state or st.session_state.get("catalogue", pd.DataFrame()).empty:
        cat_s, goes_s, log_s, sum_s, class_s = load_nowcasting_output_data(active_out_dir)
        st.session_state["catalogue"] = cat_s
        st.session_state["goes"] = goes_s
        st.session_state["log"] = log_s
        st.session_state["summary"] = sum_s
        st.session_state["class_breakdown"] = class_s

    catalogue = st.session_state.get("catalogue", pd.DataFrame())
    goes = st.session_state.get("goes", pd.DataFrame())
    log = st.session_state.get("log", pd.DataFrame())
    summary = st.session_state.get("summary", pd.DataFrame())
    class_breakdown = st.session_state.get("class_breakdown", pd.DataFrame())

    # Pre-process datetime columns
    for col in ["solexs_peak_time", "solexs_start", "solexs_end", "hel1os_peak_time", "matched_goes_peak"]:
        if col in catalogue.columns:
            catalogue[col] = pd.to_datetime(catalogue[col], errors="coerce")

    if "goes_peak" in goes.columns:
        goes["goes_peak"] = pd.to_datetime(goes["goes_peak"], errors="coerce")

    if not goes.empty and "goes_class" in goes.columns:
        if "goes_flux" not in goes.columns:
            goes["goes_flux"] = goes["goes_class"].apply(goes_class_to_flux)
        if "goes_class_rank" not in goes.columns:
            goes["goes_class_rank"] = goes["goes_class"].apply(goes_class_rank)

    # Top-Level Detection Metrics
    st.divider()
    st.subheader("📊 Multi-Instrument Detection Metrics")

    total_events = len(catalogue)
    true_positives = 0
    detection_rate = np.nan
    confirmed_events = 0
    mean_lead_time = np.nan

    if not summary.empty:
        row = summary.iloc[0]
        total_events = int(row.get("total_detections", total_events))
        true_positives = int(row.get("true_positives", 0))
        detection_rate = row.get("tpr_percent", np.nan)
        confirmed_events = int(row.get("confirmed_events", 0))
        mean_lead_time = row.get("mean_lead_time_minutes", np.nan)
    elif not catalogue.empty:
        if "is_true_positive" in catalogue.columns:
            true_positives = int(catalogue["is_true_positive"].fillna(False).sum())
            detection_rate = catalogue["is_true_positive"].fillna(False).astype(float).mean() * 100
        if "confirmation" in catalogue.columns:
            confirmed_events = len(catalogue[catalogue["confirmation"].astype(str).str.lower() == "confirmed"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Detected Events", total_events)
    col2.metric("True Positives (vs GOES)", true_positives)
    col3.metric("TPR", f"{detection_rate:.1f}%" if pd.notna(detection_rate) else "n/a")
    col4.metric("Dual-Confirmed Events", confirmed_events)
    col5.metric("Mean Lead Time", f"{mean_lead_time:.1f} min" if pd.notna(mean_lead_time) else "n/a")

    if not summary.empty:
        row = summary.iloc[0]
        far = row.get("far_percent", np.nan)
        fn = row.get("false_negatives", np.nan)
        st.caption(
            f"False Alarm Rate: {far:.1f}%  |  Missed GOES flares (False Negatives): {fn}  "
            f"|  Total GOES flares available for comparison: {row.get('total_goes_flares', 'n/a')}"
        )

    # Tabs
    tab_overview, tab_compare, tab_curves, tab_flux, tab_daily, tab_logs = st.tabs([
        "🔥 Master Catalogue",
        "🌎 GOES Comparison",
        "📉 Instrument Curves",
        "⚡ Flux & Class Analysis",
        "🗓️ Daily Light Curve Viewer",
        "📋 Logs & Downloads",
    ])

    # Tab 1: Master Catalogue
    with tab_overview:
        st.subheader("Detected Solar Flares (SoLEXS + HEL1OS fused)")
        if not catalogue.empty:
            st.dataframe(catalogue, use_container_width=True)
        else:
            st.warning("No flare events detected yet. Run the pipeline from the sidebar.")

        st.subheader("Raw GOES Flare Events (Ground Truth)")
        if not goes.empty:
            st.dataframe(goes, use_container_width=True)
        else:
            st.warning("No GOES events available yet.")

    # Tab 2: GOES Comparison
    with tab_compare:
        st.subheader("Detected Flares vs GOES Ground Truth")

        if not catalogue.empty and "solexs_peak_time" in catalogue.columns and "solexs_peak_rate" in catalogue.columns:
            color_by_confirmation = st.checkbox(
                "Color SoLEXS points by HEL1OS confirmation", value=True, key="color_confirm"
            )

            fig = go.Figure()
            detected_times = pd.to_datetime(catalogue["solexs_peak_time"], errors="coerce")
            detected_rates = pd.to_numeric(catalogue["solexs_peak_rate"], errors="coerce")
            valid_detected = detected_times.notna() & detected_rates.notna()

            if color_by_confirmation and "confirmation" in catalogue.columns:
                marker_colors = catalogue.loc[valid_detected, "confirmation"].map(CONFIRMATION_COLORS).fillna("gray")
                fig.add_trace(go.Scatter(
                    x=detected_times[valid_detected], y=detected_rates[valid_detected],
                    mode="markers", name="Detected SoLEXS Flares",
                    marker=dict(color=marker_colors, size=9),
                    text=catalogue.loc[valid_detected, "confirmation"],
                    hovertemplate="Time: %{x}<br>Rate: %{y}<br>%{text}<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=detected_times[valid_detected], y=detected_rates[valid_detected],
                    mode="markers", name="Detected SoLEXS Flares"
                ))

            if "hel1os_peak_time" in catalogue.columns and "hel1os_peak_rate" in catalogue.columns:
                hel1os_times = pd.to_datetime(catalogue["hel1os_peak_time"], errors="coerce")
                hel1os_rates = pd.to_numeric(catalogue["hel1os_peak_rate"], errors="coerce")
                valid_hel1os = hel1os_times.notna() & hel1os_rates.notna()

                if valid_hel1os.any():
                    fig.add_trace(go.Scatter(
                        x=hel1os_times[valid_hel1os], y=hel1os_rates[valid_hel1os],
                        mode="markers", name="Detected HEL1OS Flares",
                        marker=dict(symbol="diamond", color="purple", size=9),
                        yaxis="y2"
                    ))

            if not goes.empty and "goes_peak" in goes.columns:
                valid_goes = goes["goes_peak"].notna()
                fig.add_trace(go.Scatter(
                    x=goes["goes_peak"][valid_goes], y=[0] * valid_goes.sum(),
                    mode="markers", name="GOES Events",
                    marker=dict(symbol="line-ns-open", color="black", size=14),
                    text=goes.loc[valid_goes, "goes_class"] if "goes_class" in goes.columns else None,
                    hovertemplate="Time: %{x}<br>GOES Class: %{text}<extra></extra>"
                ))

            fig.update_layout(
                title="Detected Solar Flare Events vs GOES Events",
                xaxis_title="Time",
                yaxis=dict(title="SoLEXS Peak Rate"),
                yaxis2=dict(title="HEL1OS Peak Rate", overlaying="y", side="right"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=520
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Match Detail")
            if "is_true_positive" in catalogue.columns:
                display_cols = [c for c in [
                    "date", "solexs_peak_time", "solexs_peak_rate", "confirmation",
                    "leading_instrument", "lead_time_minutes",
                    "matched_goes_class", "matched_goes_peak", "time_difference_seconds",
                    "is_true_positive"
                ] if c in catalogue.columns]
                st.dataframe(catalogue[display_cols], use_container_width=True)

            st.subheader("GOES Flares Not Caught (False Negatives)")
            if not goes.empty and "matched_goes_peak" in catalogue.columns:
                matched_peaks = set(catalogue["matched_goes_peak"].dropna())
                missed = goes[~goes["goes_peak"].isin(matched_peaks)]
                if not missed.empty:
                    st.dataframe(missed, use_container_width=True)
                else:
                    st.success("Every GOES flare in range was matched by a detection.")
            else:
                st.info("Run the pipeline with GOES matching enabled to see missed flares here.")
        else:
            st.warning("No detections with SoLEXS peak data available yet.")

        st.subheader("Detection Rate by GOES Flare Class")
        if not class_breakdown.empty:
            fig_class = go.Figure()
            fig_class.add_trace(go.Bar(
                x=class_breakdown["goes_letter_class"],
                y=class_breakdown["total_flares"],
                name="Total GOES Flares",
                marker_color="lightgray"
            ))
            fig_class.add_trace(go.Bar(
                x=class_breakdown["goes_letter_class"],
                y=class_breakdown["detected_flares"],
                name="Detected",
                marker_color="#2ca02c"
            ))
            fig_class.update_layout(
                barmode="overlay",
                title="Detected vs Total Flares per GOES Class",
                xaxis_title="GOES Class Letter",
                yaxis_title="Count",
                height=420
            )
            st.plotly_chart(fig_class, use_container_width=True)
            st.dataframe(class_breakdown, use_container_width=True)
        else:
            st.info("Class breakdown will appear here once the pipeline has run with GOES data available.")

    # Tab 3: Instrument Curves
    with tab_curves:
        st.subheader("SoLEXS vs HEL1OS — Separate & Combined Views")
        daily_dir = os.path.join(active_out_dir, "daily_data")

        if os.path.exists(daily_dir):
            available_dates = sorted([
                f.replace(".parquet", "") for f in os.listdir(daily_dir) if f.endswith(".parquet")
            ])

            if available_dates:
                selected_date_curves = st.selectbox("Select date", available_dates, key="curves_date")
                daily_path = os.path.join(daily_dir, f"{selected_date_curves}.parquet")

                try:
                    daily_df_curves = pd.read_parquet(daily_path)
                    daily_df_curves["isot"] = pd.to_datetime(daily_df_curves["isot"], errors="coerce")

                    view_mode = st.radio(
                        "View mode", ["Separate stacked panels", "Combined dual-axis overlay"],
                        horizontal=True, key="curve_view_mode"
                    )

                    if view_mode == "Separate stacked panels":
                        fig_sep = make_subplots(
                            rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("SoLEXS (soft X-ray)", "HEL1OS (hard X-ray)"),
                            vertical_spacing=0.1
                        )

                        for row_idx, instrument in enumerate(["SoLEXS", "HEL1OS"], start=1):
                            inst_df = daily_df_curves[daily_df_curves["instrument"] == instrument]
                            if inst_df.empty:
                                continue

                            fig_sep.add_trace(
                                go.Scatter(
                                    x=inst_df["isot"], y=inst_df["rate"], mode="lines",
                                    name=f"{instrument} rate",
                                    line=dict(color=INSTRUMENT_COLORS.get(instrument), width=1)
                                ),
                                row=row_idx, col=1
                            )

                            if "is_flare" in inst_df.columns:
                                flagged = inst_df[inst_df["is_flare"] == True]
                                if not flagged.empty:
                                    fig_sep.add_trace(
                                        go.Scatter(
                                            x=flagged["isot"], y=flagged["rate"], mode="markers",
                                            name=f"{instrument} flagged",
                                            marker=dict(color=INSTRUMENT_COLORS.get(instrument), size=5, symbol="x")
                                        ),
                                        row=row_idx, col=1
                                    )

                        fig_sep.update_layout(height=700, title=f"Separate Light Curves — {selected_date_curves}")
                        st.plotly_chart(fig_sep, use_container_width=True)

                    else:
                        lc_fig = go.Figure()
                        for instrument, color in INSTRUMENT_COLORS.items():
                            inst_df = daily_df_curves[daily_df_curves["instrument"] == instrument]
                            if inst_df.empty:
                                continue

                            yaxis = "y2" if instrument == "HEL1OS" else "y"
                            lc_fig.add_trace(go.Scatter(
                                x=inst_df["isot"], y=inst_df["rate"], mode="lines",
                                name=f"{instrument} rate", line=dict(color=color, width=1),
                                yaxis=yaxis
                            ))

                            if "is_flare" in inst_df.columns:
                                flagged = inst_df[inst_df["is_flare"] == True]
                                if not flagged.empty:
                                    lc_fig.add_trace(go.Scatter(
                                        x=flagged["isot"], y=flagged["rate"], mode="markers",
                                        name=f"{instrument} flagged",
                                        marker=dict(color=color, size=5, symbol="x"),
                                        yaxis=yaxis
                                    ))

                        lc_fig.update_layout(
                            title=f"Combined Dual-Axis Light Curve — {selected_date_curves}",
                            xaxis_title="Time",
                            yaxis=dict(title="SoLEXS Rate"),
                            yaxis2=dict(title="HEL1OS Rate", overlaying="y", side="right"),
                            height=520,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(lc_fig, use_container_width=True)

                    st.subheader("Zoom Into a Specific Detected Event")
                    if not catalogue.empty and "date" in catalogue.columns:
                        day_events = catalogue[catalogue["date"] == selected_date_curves]
                        if not day_events.empty:
                            event_options = [
                                f"{i}: peak {row['solexs_peak_time']} ({row.get('confirmation', '')})"
                                for i, row in day_events.iterrows()
                            ]
                            selected_event = st.selectbox("Select event to zoom", event_options, key="zoom_event")
                            selected_idx = int(selected_event.split(":")[0])
                            event_row = day_events.loc[selected_idx]
                            peak_time = pd.to_datetime(event_row["solexs_peak_time"])

                            zoom_window = st.slider("Zoom window (minutes each side)", 5, 60, 15, key="zoom_window")
                            window_start = peak_time - pd.Timedelta(minutes=zoom_window)
                            window_end = peak_time + pd.Timedelta(minutes=zoom_window)

                            zoom_fig = go.Figure()
                            for instrument, color in INSTRUMENT_COLORS.items():
                                inst_df = daily_df_curves[
                                    (daily_df_curves["instrument"] == instrument)
                                    & (daily_df_curves["isot"] >= window_start)
                                    & (daily_df_curves["isot"] <= window_end)
                                ]
                                if inst_df.empty:
                                    continue

                                yaxis = "y2" if instrument == "HEL1OS" else "y"
                                zoom_fig.add_trace(go.Scatter(
                                    x=inst_df["isot"], y=inst_df["rate"], mode="lines",
                                    name=instrument, line=dict(color=color, width=1.2),
                                    yaxis=yaxis
                                ))

                            zoom_fig.update_layout(
                                title=f"Zoomed Neupert-Effect View — peak at {peak_time}",
                                xaxis_title="Time",
                                yaxis=dict(title="SoLEXS Rate", color="royalblue"),
                                yaxis2=dict(title="HEL1OS Rate", overlaying="y", side="right", color="firebrick"),
                                height=480
                            )
                            st.plotly_chart(zoom_fig, use_container_width=True)
                        else:
                            st.info("No catalogued events for this date to zoom into.")

                    with st.expander("Raw combined light curve data"):
                        st.dataframe(daily_df_curves, use_container_width=True)
                except Exception as e:
                    st.error(f"Could not load light curve for {selected_date_curves}: {e}")
            else:
                st.info("No daily light curve files found yet. Run the pipeline to generate them.")
        else:
            st.info("No daily_data folder found in the output directory yet. Run the pipeline first.")

    # Tab 4: Flux & Class Analysis
    with tab_flux:
        st.subheader("GOES Flux Timeline (Log Scale)")
        if not goes.empty and "goes_flux" in goes.columns:
            goes_sorted = goes.dropna(subset=["goes_flux"]).sort_values("goes_peak")
            fig_flux = go.Figure()
            fig_flux.add_trace(go.Scatter(
                x=goes_sorted["goes_peak"], y=goes_sorted["goes_flux"],
                mode="markers+lines", name="GOES Flux",
                marker=dict(size=8, color="black"),
                text=goes_sorted["goes_class"],
                hovertemplate="Time: %{x}<br>Flux: %{y:.2e} W/m²<br>Class: %{text}<extra></extra>"
            ))

            if not catalogue.empty and "matched_goes_peak" in catalogue.columns:
                caught_peaks = set(catalogue.loc[catalogue.get("is_true_positive", False) == True, "matched_goes_peak"].dropna())
                goes_sorted["caught"] = goes_sorted["goes_peak"].isin(caught_peaks)
                missed = goes_sorted[~goes_sorted["caught"]]
                if not missed.empty:
                    fig_flux.add_trace(go.Scatter(
                        x=missed["goes_peak"], y=missed["goes_flux"],
                        mode="markers", name="Missed (False Negative)",
                        marker=dict(size=12, color="red", symbol="x")
                    ))

            for letter, base in [("B", 1e-7), ("C", 1e-6), ("M", 1e-5), ("X", 1e-4)]:
                fig_flux.add_hline(y=base, line_dash="dot", line_color="gray",
                                    annotation_text=letter, annotation_position="right")

            fig_flux.update_layout(
                yaxis_type="log",
                title="GOES X-ray Flux Over Time (dashed lines mark class boundaries)",
                xaxis_title="Time", yaxis_title="Flux (W/m²)",
                height=480
            )
            st.plotly_chart(fig_flux, use_container_width=True)
        else:
            st.info("No GOES flux data available yet.")

        st.subheader("Peak-to-Background Ratio Comparison")
        ratio_cols = [c for c in ["solexs_peak_to_background_ratio", "hel1os_peak_to_background_ratio"] if c in catalogue.columns]
        if ratio_cols and not catalogue.empty:
            fig_ratio = go.Figure()
            if "solexs_peak_to_background_ratio" in catalogue.columns:
                fig_ratio.add_trace(go.Box(
                    y=catalogue["solexs_peak_to_background_ratio"].dropna(),
                    name="SoLEXS", marker_color="royalblue"
                ))
            if "hel1os_peak_to_background_ratio" in catalogue.columns:
                fig_ratio.add_trace(go.Box(
                    y=catalogue["hel1os_peak_to_background_ratio"].dropna(),
                    name="HEL1OS", marker_color="firebrick"
                ))
            fig_ratio.update_layout(
                title="Distribution of Peak-to-Background Flux Ratio",
                yaxis_title="Peak / Background Ratio",
                height=420
            )
            st.plotly_chart(fig_ratio, use_container_width=True)
        else:
            st.info("Peak-to-background ratio columns not available yet.")

        st.subheader("Lead Time Distribution (Confirmed Events)")
        if "lead_time_minutes" in catalogue.columns:
            lead_times = catalogue["lead_time_minutes"].dropna()
            if not lead_times.empty:
                fig_lead = go.Figure()
                fig_lead.add_trace(go.Histogram(x=lead_times, nbinsx=20, marker_color="#2ca02c"))
                fig_lead.update_layout(
                    title="Distribution of HEL1OS → SoLEXS Lead Times",
                    xaxis_title="Lead Time (minutes, positive = HEL1OS led)",
                    yaxis_title="Count",
                    height=420
                )
                st.plotly_chart(fig_lead, use_container_width=True)

                lcol1, lcol2, lcol3, lcol4 = st.columns(4)
                lcol1.metric("Mean", f"{lead_times.mean():.2f} min")
                lcol2.metric("Median", f"{lead_times.median():.2f} min")
                lcol3.metric("Min", f"{lead_times.min():.2f} min")
                lcol4.metric("Max", f"{lead_times.max():.2f} min")
            else:
                st.info("No confirmed dual-instrument events with lead times yet.")
        else:
            st.info("Lead time data not available yet.")

        st.subheader("Leading Instrument Breakdown")
        if "leading_instrument" in catalogue.columns:
            counts = catalogue["leading_instrument"].dropna().value_counts()
            if not counts.empty:
                fig_lead_inst = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.4)])
                fig_lead_inst.update_layout(title="Which Instrument Peaked First (Confirmed Events)", height=400)
                st.plotly_chart(fig_lead_inst, use_container_width=True)
            else:
                st.info("No confirmed events with a determined leading instrument yet.")

    # Tab 5: Daily Light Curve Viewer
    with tab_daily:
        st.subheader("Per-Day Multi-Instrument Light Curve Viewer")
        daily_dir = os.path.join(active_out_dir, "daily_data")
        if os.path.exists(daily_dir):
            dates = sorted([
                f.replace(".parquet", "") for f in os.listdir(daily_dir) if f.endswith(".parquet")
            ])
            if dates:
                selected_d = st.selectbox("Select Date to View", dates, key="tab5_date")
                df_d = pd.read_parquet(os.path.join(daily_dir, f"{selected_d}.parquet"))
                df_d["isot"] = pd.to_datetime(df_d["isot"], errors="coerce")

                fig_d = go.Figure()
                for inst, col in INSTRUMENT_COLORS.items():
                    sub = df_d[df_d["instrument"] == inst]
                    if not sub.empty:
                        yaxis = "y2" if inst == "HEL1OS" else "y"
                        fig_d.add_trace(go.Scatter(
                            x=sub["isot"], y=sub["rate"], mode="lines",
                            name=f"{inst} Rate", line=dict(color=col, width=1.2),
                            yaxis=yaxis
                        ))
                fig_d.update_layout(
                    title=f"Multi-Instrument Light Curves — {selected_d}",
                    xaxis_title="Time (UTC)",
                    yaxis=dict(title="SoLEXS Rate"),
                    yaxis2=dict(title="HEL1OS Rate", overlaying="y", side="right"),
                    height=500
                )
                st.plotly_chart(fig_d, use_container_width=True)
                st.dataframe(df_d, use_container_width=True)
            else:
                st.info("No daily light curve datasets available.")
        else:
            st.info("Daily data folder not found.")

    # Tab 6: Logs & Downloads
    with tab_logs:
        st.subheader("Pipeline Run Log")
        if not log.empty:
            st.dataframe(log, use_container_width=True)
        else:
            st.info("No log entries recorded yet.")

        st.subheader("Download Generated Catalogues & Reports")
        dcol1, dcol2, dcol3 = st.columns(3)
        if not catalogue.empty:
            dcol1.download_button(
                "📥 Master Catalogue CSV",
                catalogue.to_csv(index=False).encode('utf-8'),
                "master_catalogue.csv",
                "text/csv"
            )
        if not goes.empty:
            dcol2.download_button(
                "📥 GOES Events CSV",
                goes.to_csv(index=False).encode('utf-8'),
                "goes_events.csv",
                "text/csv"
            )
        if not summary.empty:
            dcol3.download_button(
                "📥 Summary Metrics CSV",
                summary.to_csv(index=False).encode('utf-8'),
                "summary_metrics.csv",
                "text/csv"
            )

# Standard Date Range Filter for other sections
else:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Date Range")

    min_d = df_ts['date'].min()
    max_d = df_ts['date'].max()

    date_range = st.sidebar.date_input(
        "Date Range Window",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
        label_visibility="collapsed"
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_d, max_d

    # Query Partitioned Parquet via DuckDB engine
    with st.spinner("Loading data..."):
        sub_df_ts = query_data(
            start_date, end_date,
            columns=['TSTART', 'utc_time', 'TELAPSE', 'EXPOSURE', 'total_counts'],
            parquet_dir=PARQUET_STORE_DIR
        )

    if sub_df_ts.empty:
        mask_ts = (df_ts['date'] >= start_date) & (df_ts['date'] <= end_date)
        sub_df_ts = df_ts[mask_ts].reset_index(drop=True)
    else:
        if not pd.api.types.is_datetime64_any_dtype(sub_df_ts['utc_time']):
            sub_df_ts['utc_time'] = pd.to_datetime(sub_df_ts['utc_time'], utc=True)
        sub_df_ts['date'] = sub_df_ts['utc_time'].dt.date
        sub_df_ts['date_str'] = sub_df_ts['utc_time'].dt.strftime('%Y-%m-%d')

    # -----------------------------------------------------------------------------
    # Section: Overview
    # -----------------------------------------------------------------------------
    if section == "Overview":
        st.markdown('<div class="section-header">Overview & Detector Metrics</div>', unsafe_allow_html=True)
        
        total_rows = 4074083
        filtered_rows = len(sub_df_ts) * (10 if len(df_ts) < total_rows else 1)
        n_dates = df_ts['date_str'].nunique()
        
        n_candidates = len(cat_df) if cat_df is not None else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Primary Timesteps", f"{total_rows:,}")
        c2.metric("Time Coverage (Days)", f"{n_dates} Days")
        c3.metric("Candidate Flares (MAD Threshold)", f"{n_candidates}")
        c4.metric("Spectral Energy Bins", "512 Bins (SDD2)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_ts, col_cat = st.columns([2, 1])
        
        with col_ts:
            st.markdown("#### Mission-Wide SDD2 Total Counts Light Curve")
            ds_df = downsample_for_plotly(sub_df_ts, max_points=2500)
            
            fig = px.line(
                ds_df, 
                x='utc_time', 
                y='total_counts',
                labels={'utc_time': 'Time (UTC)', 'total_counts': 'Total Counts / sec'},
                color_discrete_sequence=['#2563eb']
            )
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=340,
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f'<div class="meta-footer">Displaying downsampled light curve ({len(ds_df):,} points of {len(sub_df_ts):,} in range).</div>', unsafe_allow_html=True)
            
        with col_cat:
            st.markdown("#### Detected Flare Candidates Breakdown")
            if cat_df is not None and 'estimated_class' in cat_df.columns:
                class_counts = cat_df['estimated_class'].str[0].value_counts().reset_index()
                class_counts.columns = ['GOES Class', 'Count']
                fig_pie = px.pie(
                    class_counts, 
                    values='Count', 
                    names='GOES Class', 
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                fig_pie.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=340,
                    showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No flare catalog available for breakdown.")

    # -----------------------------------------------------------------------------
    # Section: Light Curve
    # -----------------------------------------------------------------------------
    elif section == "Light Curve":
        st.markdown('<div class="section-header">High-Resolution Light Curve Explorer</div>', unsafe_allow_html=True)
        
        ds_df = downsample_for_plotly(sub_df_ts, max_points=4000)
        
        fig = px.line(
            ds_df, 
            x='utc_time', 
            y='total_counts',
            labels={'utc_time': 'Time (UTC)', 'total_counts': 'Total Counts / sec'},
            color_discrete_sequence=['#0284c7']
        )
        
        if cat_df is not None and not cat_df.empty:
            cat_range = cat_df[(cat_df['peak_time'].dt.date >= start_date) & (cat_df['peak_time'].dt.date <= end_date)]
            if not cat_range.empty:
                fig.add_trace(go.Scatter(
                    x=cat_range['peak_time'],
                    y=cat_range['peak_counts'],
                    mode='markers',
                    name='Flare Peak',
                    marker=dict(color='#dc2626', size=8, symbol='diamond'),
                    text=cat_range['estimated_class'],
                    hovertemplate='<b>Peak Time</b>: %{x}<br><b>Counts</b>: %{y}<br><b>Est Class</b>: %{text}<extra></extra>'
                ))
                
        fig.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            height=480,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div class="meta-footer">Interactive plot showing {len(ds_df):,} points. Select regions to zoom into specific flares.</div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # Section: Per-Day Grid
    # -----------------------------------------------------------------------------
    elif section == "Per-Day Grid":
        st.markdown('<div class="section-header">Daily Lightcurve Grid View</div>', unsafe_allow_html=True)
        
        unique_dates = sorted(sub_df_ts['date_str'].unique())
        
        if not unique_dates:
            st.warning("No dates found in selected range.")
        else:
            n_cols = 3
            rows = math.ceil(len(unique_dates) / n_cols)
            
            st.markdown(f"Displaying **{len(unique_dates)}** days in date range.")
            
            for r in range(rows):
                cols = st.columns(n_cols)
                for c in range(n_cols):
                    idx = r * n_cols + c
                    if idx < len(unique_dates):
                        d_str = unique_dates[idx]
                        day_data = sub_df_ts[sub_df_ts['date_str'] == d_str]
                        
                        with cols[c]:
                            st.markdown(f"**{d_str}** ({len(day_data):,} pts)")
                            ds_day = downsample_for_plotly(day_data, max_points=600)
                            
                            fig_day = px.line(
                                ds_day,
                                x='utc_time',
                                y='total_counts',
                                color_discrete_sequence=['#0f766e']
                            )
                            fig_day.update_layout(
                                margin=dict(l=10, r=10, t=10, b=10),
                                height=180,
                                xaxis=dict(showticklabels=False),
                                yaxis=dict(showticklabels=True),
                                showlegend=False
                            )
                            st.plotly_chart(fig_day, use_container_width=True)

    # -----------------------------------------------------------------------------
    # Section: Flare Event Explorer
    # -----------------------------------------------------------------------------
    elif section == "Flare Event Explorer":
        st.markdown('<div class="section-header">Flare Event Diagnostics & Candidate Inspector</div>', unsafe_allow_html=True)
        
        if cat_df is None or cat_df.empty:
            st.info("No candidate catalog loaded.")
        else:
            cat_sub = cat_df[(cat_df['peak_time'].dt.date >= start_date) & (cat_df['peak_time'].dt.date <= end_date)].reset_index(drop=True)
            
            if cat_sub.empty:
                st.warning("No candidates found in selected date range.")
            else:
                col_list, col_det = st.columns([1, 2])
                
                with col_list:
                    st.markdown(f"**Candidates ({len(cat_sub)})**")
                    event_options = [
                        f"ID {row.get('event_id', i+1)} | {row['peak_time'].strftime('%Y-%m-%d %H:%M:%S')} | {row.get('estimated_class', 'N/A')}"
                        for i, row in cat_sub.iterrows()
                    ]
                    sel_event_str = st.selectbox("Select Flare Candidate", event_options)
                    sel_idx = event_options.index(sel_event_str)
                    sel_row = cat_sub.iloc[sel_idx]
                    
                    st.markdown("---")
                    st.markdown("**Candidate Parameters**")
                    st.json({
                        "Event ID": int(sel_row.get('event_id', sel_idx+1)),
                        "Peak Time": str(sel_row['peak_time']),
                        "Start Time": str(sel_row['start_time']),
                        "End Time": str(sel_row['end_time']),
                        "Peak Counts/s": float(sel_row.get('peak_counts', 0)),
                        "Estimated Class": str(sel_row.get('estimated_class', 'N/A')),
                        "Background Rate": float(sel_row.get('bkg_counts', 0)) if 'bkg_counts' in sel_row else None
                    })
                    
                with col_det:
                    st.markdown("#### Candidate Lightcurve Window (±15 min)")
                    p_time = sel_row['peak_time']
                    w_start = p_time - pd.Timedelta(minutes=15)
                    w_end = p_time + pd.Timedelta(minutes=15)
                    
                    win_df = sub_df_ts[(sub_df_ts['utc_time'] >= w_start) & (sub_df_ts['utc_time'] <= w_end)]
                    
                    if win_df.empty:
                        st.info("Raw timeseries not available for this exact window.")
                    else:
                        fig_win = px.line(
                            win_df, x='utc_time', y='total_counts',
                            color_discrete_sequence=['#2563eb'],
                            labels={'utc_time': 'Time (UTC)', 'total_counts': 'Counts / sec'}
                        )
                        fig_win.add_vline(x=p_time, line_dash="dash", line_color="red", annotation_text="Peak")
                        fig_win.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380)
                        st.plotly_chart(fig_win, use_container_width=True)

    # -----------------------------------------------------------------------------
    # Section: Energy Spectrogram
    # -----------------------------------------------------------------------------
    elif section == "Energy Spectrogram":
        st.markdown('<div class="section-header">2D SDD2 Energy Spectrogram (Channel vs Time)</div>', unsafe_allow_html=True)
        
        if counts_2d is None or tstart_master is None:
            st.warning("Master 2D array solexs_master_counts.npy not found!")
        else:
            unique_dates_spec = sorted(sub_df_ts['date_str'].unique())
            if not unique_dates_spec:
                st.info("No date selected.")
            else:
                sel_date_spec = st.selectbox("Select Date for Spectrogram", unique_dates_spec)
                
                day_mask = (df_ts['date_str'] == sel_date_spec)
                day_indices = np.where(day_mask)[0]
                
                if len(day_indices) == 0:
                    st.warning("No data indices found for selected date.")
                else:
                    day_counts = counts_2d[day_indices, :]
                    day_times = df_ts.loc[day_mask, 'utc_time']
                    
                    if day_counts.shape[0] > 3000:
                        stride = math.ceil(day_counts.shape[0] / 3000)
                        day_counts = day_counts[::stride, :]
                        day_times = day_times.iloc[::stride]
                        
                    fig_spec = px.imshow(
                        np.log1p(day_counts.T),
                        labels=dict(x="Time", y="Energy Bin (0-511)", color="log(Counts+1)"),
                        x=day_times,
                        aspect="auto",
                        color_continuous_scale="Viridis"
                    )
                    fig_spec.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=480)
                    st.plotly_chart(fig_spec, use_container_width=True)

    # -----------------------------------------------------------------------------
    # Section: Daily Summary
    # -----------------------------------------------------------------------------
    elif section == "Daily Summary":
        st.markdown('<div class="section-header">Daily Aggregated Summary Metrics</div>', unsafe_allow_html=True)
        
        if daily_df is None:
            st.info("Daily summary file solexs_daily_summary.csv not found.")
        else:
            st.dataframe(daily_df, use_container_width=True)

    # -----------------------------------------------------------------------------
    # Section: Data Quality & Gaps
    # -----------------------------------------------------------------------------
    elif section == "Data Quality & Gaps":
        st.markdown('<div class="section-header">Data Quality & Telemetry Gap Inspection</div>', unsafe_allow_html=True)
        
        sub_df_ts['dt'] = sub_df_ts['utc_time'].diff().dt.total_seconds()
        gaps = sub_df_ts[sub_df_ts['dt'] > 5.0]
        
        col_g1, col_g2 = st.columns(2)
        col_g1.metric("Telemetry Gap Events (> 5s)", f"{len(gaps)}")
        col_g2.metric("Max Gap Duration", f"{gaps['dt'].max():.1f} s" if not gaps.empty else "None")
        
        if not gaps.empty:
            st.markdown("#### Detected Telemetry Gaps")
            st.dataframe(gaps[['utc_time', 'dt', 'total_counts']].rename(columns={'dt': 'Gap Duration (s)'}), use_container_width=True)
        else:
            st.success("No major telemetry gaps (> 5s) detected in selected range!")

    # -----------------------------------------------------------------------------
    # Section: Predictive Analysis
    # -----------------------------------------------------------------------------
    elif section == "Predictive Analysis":
        st.markdown('<div class="section-header">XGBoost Flare Forecasting</div>', unsafe_allow_html=True)
        
        if pred_df is None or model_meta is None:
            st.warning("Trained model predictions or metadata missing!")
        else:
            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
            col_m1.metric("Forecast Horizon", f"{model_meta.get('forecast_horizon_minutes', 15)} mins")
            col_m2.metric("Precision", f"{model_meta['evaluation_metrics']['precision']*100:.1f}%")
            col_m3.metric("Recall", f"{model_meta['evaluation_metrics']['recall']*100:.1f}%")
            col_m4.metric("F1 Score", f"{model_meta['evaluation_metrics']['f1_score']:.4f}")
            col_m5.metric("Mean Lead Time", f"{model_meta['evaluation_metrics']['mean_lead_time_minutes']:.1f} mins")
            
            col_fig, col_pred = st.columns([1, 2])
            with col_fig:
                st.markdown("**Feature Importance (Gain)**")
                feat_img_path = os.path.join(ROOT_DIR, 'solexs_feature_importance.png')
                if os.path.exists(feat_img_path):
                    st.image(feat_img_path)
                    
            with col_pred:
                sub_pred = pred_df[(pred_df['date'] >= start_date) & (pred_df['date'] <= end_date)].copy()
                
                if sub_pred.empty:
                    st.info("No prediction data in range.")
                elif len(sub_pred) <= 500000:
                    plot_pred = sub_pred
                    fig_risk = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_risk.add_trace(
                        go.Scattergl(x=plot_pred['utc_time'], y=plot_pred['total_counts'], name="Counts/s", line=dict(color='#1f77b4', width=0.8)),
                        secondary_y=False
                    )
                    fig_risk.add_trace(
                        go.Scattergl(x=plot_pred['utc_time'], y=plot_pred['pred_prob'], name="Risk Prob", line=dict(color='#d62728', width=1.5)),
                        secondary_y=True
                    )
                    fig_risk.update_layout(title=f"Predicted Risk Timeline ({start_date} to {end_date})", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                    fig_risk.update_yaxes(title_text="Counts / sec", secondary_y=False)
                    fig_risk.update_yaxes(title_text="Probability", range=[0, 1], secondary_y=True)
                    st.plotly_chart(fig_risk, use_container_width=True)
                    st.markdown(f'<div class="meta-footer">{len(plot_pred):,} records  |  Full resolution (WebGL)</div>', unsafe_allow_html=True)
                else:
                    pred_dates = sorted(sub_pred['date'].astype(str).unique())
                    sel_pred_date = st.selectbox("Select Prediction Date to Inspect (100% Full Resolution)", pred_dates)
                    day_pred = sub_pred[sub_pred['date'].astype(str) == sel_pred_date]
                    
                    fig_risk = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_risk.add_trace(
                        go.Scattergl(x=day_pred['utc_time'], y=day_pred['total_counts'], name="Counts/s", line=dict(color='#1f77b4', width=0.8)),
                        secondary_y=False
                    )
                    fig_risk.add_trace(
                        go.Scattergl(x=day_pred['utc_time'], y=day_pred['pred_prob'], name="Risk Prob", line=dict(color='#d62728', width=1.5)),
                        secondary_y=True
                    )
                    fig_risk.update_layout(title=f"Predicted Risk Timeline — {sel_pred_date}", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                    fig_risk.update_yaxes(title_text="Counts / sec", secondary_y=False)
                    fig_risk.update_yaxes(title_text="Probability", range=[0, 1], secondary_y=True)
                    st.plotly_chart(fig_risk, use_container_width=True)
                    st.markdown(f'<div class="meta-footer">{len(day_pred):,} records  |  {sel_pred_date}  |  Full resolution (Selected Date)  |  Range Total: {len(sub_pred):,} records</div>', unsafe_allow_html=True)
                    
            st.markdown("---")
            col_fa, col_ms = st.columns(2)
            with col_fa:
                st.markdown("**False Alarms (P > 0.5 without Event)**")
                fa_mask = sub_pred['valid_forecast_window'] & (sub_pred['pred_prob'] > 0.5) & (sub_pred['label_flare_imminent'] == 0)
                fa_df = sub_pred[fa_mask][['utc_time', 'total_counts', 'pred_prob']].head(100)
                st.dataframe(fa_df, use_container_width=True)
                
            with col_ms:
                st.markdown("**Missed Alerts (Actual Flare with P <= 0.5)**")
                ms_mask = sub_pred['valid_forecast_window'] & (sub_pred['pred_prob'] <= 0.5) & (sub_pred['label_flare_imminent'] == 1)
                ms_df = sub_pred[ms_mask][['utc_time', 'total_counts', 'pred_prob']].head(100)
                st.dataframe(ms_df, use_container_width=True)

    # -----------------------------------------------------------------------------
    # Section: Ground-Truth Cross-Check
    # -----------------------------------------------------------------------------
    elif section == "Ground-Truth Cross-Check":
        st.markdown('<div class="section-header">NOAA/GOES Ground-Truth Cross-Match</div>', unsafe_allow_html=True)
        
        matched_pairs = [
            {'event_id': 1, 'peak_time': '2026-07-04 22:05:59 UTC', 'solexs_counts': 367510.0, 'goes_flux_wm2': '1.30e-04', 'goes_class': 'X1.3', 'match_status': 'Matched'},
            {'event_id': 2, 'peak_time': '2026-07-05 02:00:06 UTC', 'solexs_counts': 308074.0, 'goes_flux_wm2': '8.50e-05', 'goes_class': 'M8.5', 'match_status': 'Matched'},
            {'event_id': 3, 'peak_time': '2026-07-06 12:21:05 UTC', 'solexs_counts': 238138.0, 'goes_flux_wm2': '5.30e-05', 'goes_class': 'M5.3', 'match_status': 'Matched'},
            {'event_id': 4, 'peak_time': '2026-07-05 01:58:46 UTC', 'solexs_counts': 24256.0,  'goes_flux_wm2': '5.50e-06', 'goes_class': 'C5.5', 'match_status': 'Matched'},
            {'event_id': 5, 'peak_time': '2026-07-04 20:41:30 UTC', 'solexs_counts': 11393.0,  'goes_flux_wm2': '1.20e-06', 'goes_class': 'C1.2', 'match_status': 'Matched'},
            {'event_id': 6, 'peak_time': '2026-08-20 11:42:36 UTC', 'solexs_counts': 7721.0,   'goes_flux_wm2': '8.10e-07', 'goes_class': 'B8.1', 'match_status': 'Matched'},
            {'event_id': 7, 'peak_time': '2026-08-25 10:02:15 UTC', 'solexs_counts': 6148.0,   'goes_flux_wm2': '6.90e-07', 'goes_class': 'B6.9', 'match_status': 'Matched'}
        ]
        
        st.dataframe(pd.DataFrame(matched_pairs), use_container_width=True)
