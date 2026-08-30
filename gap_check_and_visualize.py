import os
import sys
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for file generation
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def compute_physical_flux(df, counts_2d, A_eff=1.0e-5):
    """
    Compute physical solar X-ray flux in W/m^2 across the 340 channels of SoLEXS SDD2.
    Formula:
      E_i [keV] = 1.0 + (i + 0.5) * (29.0 / 340.0)
      E_i [Joules] = E_i [keV] * 1.60218e-16 J/keV
      P(t) [Watts] = sum_i (COUNTS_i(t) * E_i [J]) / EXPOSURE(t)
      Flux(t) [W/m^2] = P(t) / A_eff
    """
    print("\nComputing physical solar X-ray flux (W/m^2) and GOES classifications...")
    channels = np.arange(340)
    e_min, e_max = 1.0, 30.0
    de = (e_max - e_min) / 340.0
    e_center_kev = e_min + (channels + 0.5) * de
    e_center_joules = e_center_kev * 1.60218e-16  # J/photon
    
    exposure = df['EXPOSURE'].values
    exposure = np.where(exposure > 0, exposure, 1.0)
    
    chunk_size = 500000
    flux_chunks = []
    for i in range(0, len(df), chunk_size):
        chunk_counts = counts_2d[i : i + chunk_size]
        chunk_exp = exposure[i : i + chunk_size]
        chunk_energy_per_sec = np.dot(chunk_counts, e_center_joules) / chunk_exp
        chunk_flux = chunk_energy_per_sec / A_eff
        flux_chunks.append(chunk_flux)
        
    flux_wm2 = np.concatenate(flux_chunks)
    df['flux_wm2'] = flux_wm2
    return df

def get_goes_class(flux):
    """
    Convert physical X-ray flux in W/m^2 to standard GOES Solar Flare Classification.
    X-Class: >= 1e-4 W/m^2
    M-Class: 1e-5 to 1e-4 W/m^2
    C-Class: 1e-6 to 1e-5 W/m^2
    B-Class: 1e-7 to 1e-6 W/m^2
    A-Class: < 1e-7 W/m^2
    """
    if flux >= 1e-4:
        return f"X{flux/1e-4:.1f}"
    elif flux >= 1e-5:
        return f"M{flux/1e-5:.1f}"
    elif flux >= 1e-6:
        return f"C{flux/1e-6:.1f}"
    elif flux >= 1e-7:
        return f"B{flux/1e-7:.1f}"
    else:
        val = flux / 1e-8
        return f"A{val:.1f}"

def load_master_dataset(root_dir):
    """Load the master parquet dataframe and 2D npy counts array."""
    parquet_path = os.path.join(root_dir, 'solexs_master_timeseries.parquet')
    npy_path = os.path.join(root_dir, 'solexs_master_counts.npy')
    
    if not os.path.exists(parquet_path) or not os.path.exists(npy_path):
        raise FileNotFoundError(
            f"Master dataset files not found. Run batch_load.py first!\n"
            f"Missing: {parquet_path} or {npy_path}"
        )
        
    print(f"Loading master timeseries from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    
    print(f"Loading master 340-channel counts from {npy_path}...")
    counts_2d = np.load(npy_path, mmap_mode='r')
    
    # Ensure utc_time is datetime and create date_str
    df['utc_time'] = pd.to_datetime(df['utc_time'], utc=True)
    df['date_str'] = df['utc_time'].dt.strftime('%Y-%m-%d')
    
    # Compute physical flux
    df = compute_physical_flux(df, counts_2d)
    return df, counts_2d

def run_gap_analysis(df):
    """
    Analyze gaps in TSTART timeline (>60s), missing calendar dates,
    partial-coverage dates, and telemetry dropout patterns.
    """
    print("\n" + "=" * 60)
    print("STEP 3: DATA QUALITY & TIMELINE GAP ANALYSIS")
    print("=" * 60)
    
    # Sort just in case
    df = df.sort_values('TSTART').reset_index(drop=True)
    
    # Compute time differences between consecutive rows
    t_diff = df['TSTART'].diff()
    gap_mask = t_diff > 60.0
    
    gaps_df = pd.DataFrame({
        'gap_start_utc': df['utc_time'].shift(1)[gap_mask],
        'gap_end_utc': df['utc_time'][gap_mask],
        'gap_duration_sec': t_diff[gap_mask]
    }).reset_index(drop=True)
    
    print(f"\nTotal TSTART gaps > 60 seconds detected: {len(gaps_df)}")
    if len(gaps_df) > 0:
        print("\nFull Gap Breakdown Table (First 25 shown for display):")
        print("-" * 65)
        print(f"{'Gap #':<6} | {'Gap Start (UTC)':<22} | {'Gap End (UTC)':<22} | {'Duration (s)':<12}")
        print("-" * 65)
        for idx, row in gaps_df.head(25).iterrows():
            st_str = row['gap_start_utc'].strftime('%Y-%m-%d %H:%M:%S')
            en_str = row['gap_end_utc'].strftime('%Y-%m-%d %H:%M:%S')
            dur = row['gap_duration_sec']
            print(f"{idx+1:<6} | {st_str:<22} | {en_str:<22} | {dur:<12.1f}")
        if len(gaps_df) > 25:
            print(f"... and {len(gaps_df)-25} more gaps > 60s recorded.")
        print("-" * 65)
    else:
        print("No gaps > 60 seconds found in the continuous timeline.")
        
    # Check date coverage
    present_dates = sorted(df['date_str'].unique())
    
    min_date = df['utc_time'].min().floor('D')
    max_date = df['utc_time'].max().floor('D')
    all_possible_dates = pd.date_range(min_date, max_date, freq='D').strftime('%Y-%m-%d').tolist()
    
    missing_dates = sorted(list(set(all_possible_dates) - set(present_dates)))
    
    print(f"\nTimeline Span: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({len(all_possible_dates)} total calendar days)")
    print(f"Present Calendar Dates: {len(present_dates)}")
    print(f"Missing Calendar Dates ({len(missing_dates)}):")
    if missing_dates:
        print("  " + ", ".join(missing_dates))
    else:
        print("  None (All calendar dates in range have data)")
        
    # Daily row counts (expected ~86,400 per day)
    daily_counts = df.groupby('date_str').size()
    partial_dates = daily_counts[daily_counts < 75000]
    
    print(f"\nPartial-Coverage Days (< 75,000 rows/day): {len(partial_dates)}")
    if len(partial_dates) > 0:
        for d, count in partial_dates.items():
            pct = (count / 86400.0) * 100
            print(f"  - Date: {d} | Row Count: {count:,} / 86,400 ({pct:.1f}% coverage)")
            
    # Classify gaps per date
    if len(gaps_df) > 0:
        gaps_df['date_str'] = gaps_df['gap_start_utc'].dt.strftime('%Y-%m-%d')
        gaps_per_date = gaps_df.groupby('date_str').size()
        dense_dropout_dates = gaps_per_date[gaps_per_date >= 3].index.tolist()
        
        print("\nData Quality Dropout Classification:")
        print(f"  1. Clean Missing Dates (Not Downloaded / Data Not Present): {missing_dates}")
        print(f"  2. Densely-Gappy Dates (Telemetry / Sensor Dropout): {dense_dropout_dates}")

    return gaps_df, missing_dates, present_dates

def plot_full_lightcurve(df, root_dir):
    """Plot full multi-day light curve with count rate and physical flux axes."""
    print("\nRendering Full Multi-Day Light Curve plot...")
    fig, ax1 = plt.subplots(figsize=(16, 4.5), dpi=150)
    
    color = '#1f77b4'
    ax1.plot(df['utc_time'], df['total_counts'], color=color, linewidth=0.4, alpha=0.85, label='Counts/sec')
    ax1.set_xlabel("UTC Time", fontsize=11, labelpad=8)
    ax1.set_ylabel("Total Counts / sec", fontsize=11, color=color, labelpad=8)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    
    # Secondary axis for physical flux in W/m^2
    ax2 = ax1.twinx()
    color_flux = '#d62728'
    ax2.plot(df['utc_time'], df['flux_wm2'], color=color_flux, linewidth=0.4, alpha=0.25)
    ax2.set_ylabel("Physical Flux (W/m²)", fontsize=11, color=color_flux, labelpad=8)
    ax2.tick_params(axis='y', labelcolor=color_flux)
    ax2.set_yscale('log')
    
    plt.title("SoLEXS SDD2 — Full Multi-Day X-ray Light Curve & Physical Flux", fontsize=14, fontweight='bold', pad=10)
    plt.tight_layout()
    
    out_path = os.path.join(root_dir, 'solexs_full_lightcurve.png')
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")

def plot_per_day_grid(df, present_dates, root_dir):
    """Plot per-day light curve grid (small multiples)."""
    print("\nRendering Per-Day Light Curve Grid plot...")
    num_dates = len(present_dates)
    cols = 5
    rows = math.ceil(num_dates / cols)
    
    fig, axes = plt.subplots(rows, cols, figsize=(20, 2.5 * rows), dpi=120, sharey=True)
    axes = axes.flatten() if num_dates > 1 else [axes]
    
    for idx, date_str in enumerate(present_dates):
        ax = axes[idx]
        sub_df = df[df['date_str'] == date_str]
        ax.plot(sub_df['utc_time'], sub_df['total_counts'], color='#2ca02c', linewidth=0.5)
        ax.set_title(date_str, fontsize=10, fontweight='bold', pad=4)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.grid(True, linestyle=':', alpha=0.5)
        
    # Hide unused subplots
    for idx in range(num_dates, len(axes)):
        fig.delaxes(axes[idx])
        
    fig.suptitle("SoLEXS SDD2 — Per-Day Light Curves", fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    out_path = os.path.join(root_dir, 'solexs_per_day_lightcurves.png')
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")

def detect_flare_candidates(df, root_dir):
    """
    Statistically honest rolling MAD-based flare candidate detection.
    WINDOW_SECONDS = 1800 (30 min centered window)
    min_periods = 30
    THRESHOLD_MAD = 6.0
    robust_sigma = MAD * 1.4826
    """
    print("\n" + "=" * 60)
    print("STEP 5: ROBUST MAD-BASED FLARE CANDIDATE DETECTION")
    print("=" * 60)
    
    WINDOW_SECONDS = 1800
    MIN_PERIODS = 30
    THRESHOLD_MAD = 6.0
    
    print(f"Parameters: Window = {WINDOW_SECONDS}s (30m centered), min_periods = {MIN_PERIODS}, Threshold = {THRESHOLD_MAD} * MAD_sigma")
    
    temp_df = df[['utc_time', 'total_counts', 'TSTART', 'flux_wm2']].copy()
    temp_df = temp_df.set_index('utc_time')
    
    # 1. Local background = rolling median
    print("Calculating rolling median background...")
    rolling_obj = temp_df['total_counts'].rolling(f'{WINDOW_SECONDS}s', center=True, min_periods=MIN_PERIODS)
    bg = rolling_obj.median().values
    
    # 2. Local MAD = rolling median of |counts - background|
    print("Calculating rolling Median Absolute Deviation (MAD)...")
    abs_diff = pd.Series(np.abs(temp_df['total_counts'].values - bg), index=temp_df.index)
    mad = abs_diff.rolling(f'{WINDOW_SECONDS}s', center=True, min_periods=MIN_PERIODS).median().values
    
    # 3. Robust sigma
    robust_sigma = mad * 1.4826
    robust_sigma = np.nan_to_num(robust_sigma, nan=1e-6)
    robust_sigma[robust_sigma == 0] = 1e-6
    
    # 4. Flag candidates
    counts_vals = temp_df['total_counts'].values
    residual = counts_vals - bg
    is_candidate = residual > (THRESHOLD_MAD * robust_sigma)
    
    df['background'] = bg
    df['robust_sigma'] = robust_sigma
    df['is_candidate'] = is_candidate
    
    candidate_seconds = is_candidate.sum()
    pct_candidate = (candidate_seconds / len(df)) * 100
    print(f"\nCandidate Seconds Flagged: {candidate_seconds:,} / {len(df):,} ({pct_candidate:.4f}%)")
    
    # Plot flare detection result
    print("Rendering Flare Candidate Detection overview plot...")
    plt.figure(figsize=(16, 5), dpi=150)
    plt.plot(df['utc_time'], df['total_counts'], color='#1f77b4', linewidth=0.4, alpha=0.7, label='Measured Counts/s')
    plt.plot(df['utc_time'], df['background'], color='#ff7f0e', linewidth=1.2, alpha=0.9, label='Rolling Background (30m Median)')
    
    if candidate_seconds > 0:
        cand_df = df[df['is_candidate']]
        plt.scatter(cand_df['utc_time'], cand_df['total_counts'], color='#d62728', s=8, zorder=5, label=f'Flare Candidates ({THRESHOLD_MAD}σ MAD)')
        
    plt.title("SoLEXS — Robust (MAD-based) Flare Detection", fontsize=14, fontweight='bold', pad=10)
    plt.xlabel("UTC Time", fontsize=11, labelpad=8)
    plt.ylabel("Total Counts / sec", fontsize=11, labelpad=8)
    plt.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.tight_layout()
    
    out_path = os.path.join(root_dir, 'solexs_flare_detection.png')
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")
    
    # Discrete event grouping
    events = []
    if candidate_seconds > 0:
        group_id = (~df['is_candidate']).cumsum()[df['is_candidate']]
        
        for g_id, group in df[df['is_candidate']].groupby(group_id):
            start_time = group['utc_time'].min()
            end_time = group['utc_time'].max()
            start_tstart = group['TSTART'].min()
            end_tstart = group['TSTART'].max()
            duration_sec = int(end_tstart - start_tstart + 1)
            
            peak_idx = group['total_counts'].idxmax()
            peak_row = df.loc[peak_idx]
            peak_time = peak_row['utc_time']
            peak_counts = peak_row['total_counts']
            peak_flux = peak_row['flux_wm2']
            bg_at_peak = peak_row['background']
            goes_cls = get_goes_class(peak_flux)
            
            events.append({
                'event_id': len(events) + 1,
                'start_time': start_time,
                'end_time': end_time,
                'duration_sec': duration_sec,
                'peak_time': peak_time,
                'peak_counts': peak_counts,
                'peak_flux_wm2': peak_flux,
                'goes_class': goes_cls,
                'background_at_peak': bg_at_peak,
                'peak_row_index': peak_idx
            })
            
    events_df = pd.DataFrame(events)
    if not events_df.empty:
        events_df = events_df.sort_values('peak_counts', ascending=False).reset_index(drop=True)
        events_df['event_id'] = np.arange(1, len(events_df) + 1)
        
    print(f"\nTotal Discrete Flare Candidate Events Grouped: {len(events_df)}")
    return events_df, df

def generate_per_event_diagnostics(events_df, df, counts_2d, root_dir, max_plots=50):
    """
    Step 6: Per-event diagnostics.
    Zoomed light curve (+-10 min) and peak 340-channel spectrum vs quiet-time median spectrum.
    Renders diagnostic plots for top events sorted by peak counts.
    """
    print("\n" + "=" * 60)
    print("STEP 6: PER-EVENT DIAGNOSTIC PLOTS")
    print("=" * 60)
    
    if events_df.empty:
        print("Zero flare candidate events detected. Skipping per-event diagnostic plots.")
        return
        
    print("Calculating overall quiet-time median spectrum across dataset...")
    quiet_mask = ~df['is_candidate'].values
    if quiet_mask.sum() > 0:
        quiet_indices = np.where(quiet_mask)[0]
        if len(quiet_indices) > 500000:
            sample_idx = np.random.choice(quiet_indices, size=500000, replace=False)
            quiet_median_spectrum = np.nanmedian(counts_2d[sample_idx], axis=0)
        else:
            quiet_median_spectrum = np.nanmedian(counts_2d[quiet_indices], axis=0)
    else:
        quiet_median_spectrum = np.nanmedian(counts_2d[:], axis=0)
        
    plots_df = events_df.head(max_plots)
    print(f"Generating diagnostic plots for top {len(plots_df)} peak candidate events...")
    
    for idx, event in plots_df.iterrows():
        e_id = int(event['event_id'])
        pk_time = event['peak_time']
        pk_counts = event['peak_counts']
        pk_flux = event['peak_flux_wm2']
        goes_cls = event['goes_class']
        pk_row_idx = int(event['peak_row_index'])
        
        # 10 minute window around event peak
        win_start = pk_time - pd.Timedelta(minutes=10)
        win_end = pk_time + pd.Timedelta(minutes=10)
        
        sub_df = df[(df['utc_time'] >= win_start) & (df['utc_time'] <= win_end)]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4.5), dpi=130)
        
        # 1. Zoomed Light Curve
        ax1.plot(sub_df['utc_time'], sub_df['total_counts'], color='#1f77b4', linewidth=1.0, label='Total Counts/s')
        ax1.axvline(pk_time, color='#d62728', linestyle='--', linewidth=1.2, label=f'Peak: {pk_counts:.0f} c/s ({goes_cls})')
        ax1.set_title(f"Event {e_id} ({goes_cls}) — Zoomed Light Curve (±10 min)", fontsize=11, fontweight='bold')
        ax1.set_xlabel("UTC Time", fontsize=10)
        ax1.set_ylabel("Total Counts / sec", fontsize=10)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend(loc='upper right')
        
        # 2. Peak Spectrum vs Quiet Spectrum
        peak_spectrum = counts_2d[pk_row_idx]
        channels = np.arange(340)
        
        ax2.plot(channels, peak_spectrum, color='#d62728', linewidth=1.2, label='Peak Second Spectrum')
        ax2.plot(channels, quiet_median_spectrum, color='#7f7f7f', linewidth=1.0, linestyle=':', label='Dataset Quiet Median Spectrum')
        ax2.set_title(f"Event {e_id} — 340-Channel Energy Spectrum", fontsize=11, fontweight='bold')
        ax2.set_xlabel("Energy Channel (0-339)", fontsize=10)
        ax2.set_ylabel("Counts", fontsize=10)
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc='upper right')
        
        pk_time_str = pk_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        fig.suptitle(f"Event {e_id} — Peak {pk_counts:.0f} c/s ({pk_flux:.2e} W/m², GOES Class {goes_cls}) at {pk_time_str}", fontsize=12, fontweight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        out_path = os.path.join(root_dir, f'solexs_event_{e_id}_diagnostic.png')
        plt.savefig(out_path)
        plt.close(fig)
        if idx < 10 or (idx + 1) % 10 == 0:
            print(f"Rendered diagnostic plot for Event {e_id} -> {os.path.basename(out_path)}")

def generate_daily_summary_and_reporting(df, events_df, gaps_df, missing_dates, root_dir):
    """
    Step 7: Daily summary table, bar plot, event catalog export, and reporting statistics.
    """
    print("\n" + "=" * 60)
    print("STEP 7: DAILY SUMMARY, CATALOG EXPORT & REPORTING")
    print("=" * 60)
    
    # Group by calendar date for daily summary table
    daily_grp = df.groupby('date_str')
    daily_summary = pd.DataFrame({
        'mean_counts': daily_grp['total_counts'].mean(),
        'median_counts': daily_grp['total_counts'].median(),
        'max_counts': daily_grp['total_counts'].max(),
        'std_counts': daily_grp['total_counts'].std(),
        'mean_flux_wm2': daily_grp['flux_wm2'].mean(),
        'max_flux_wm2': daily_grp['flux_wm2'].max(),
        'max_goes_class': [get_goes_class(f) for f in daily_grp['flux_wm2'].max()],
        'n_seconds': daily_grp['total_counts'].count()
    }).reset_index()
    
    daily_summary_csv = os.path.join(root_dir, 'solexs_daily_summary.csv')
    daily_summary.to_csv(daily_summary_csv, index=False)
    print(f"\nSaved daily summary table to: {daily_summary_csv}")
    
    print("\nFull Daily Summary Table (`solexs_daily_summary.csv`):")
    print("=" * 110)
    print(daily_summary.to_string(index=False))
    print("=" * 110)
    
    # Plot Daily Peak X-ray Activity bar chart
    print("\nRendering Daily Peak X-ray Activity bar chart...")
    fig, ax1 = plt.subplots(figsize=(14, 5), dpi=150)
    
    color = '#1f77b4'
    bars = ax1.bar(daily_summary['date_str'], daily_summary['max_counts'], color=color, edgecolor='black', linewidth=0.5, label='Peak Counts/s')
    ax1.set_xlabel("Calendar Date", fontsize=11, labelpad=8)
    ax1.set_ylabel("Peak Total Counts / sec", fontsize=11, color=color, labelpad=8)
    ax1.tick_params(axis='x', rotation=60, labelsize=8)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)
    
    # Secondary axis for physical flux (W/m^2)
    ax2 = ax1.twinx()
    color_flux = '#d62728'
    ax2.plot(daily_summary['date_str'], daily_summary['max_flux_wm2'], color=color_flux, marker='o', linewidth=1.5, label='Peak Flux (W/m²)')
    ax2.set_ylabel("Peak Physical Flux (W/m²)", fontsize=11, color=color_flux, labelpad=8)
    ax2.tick_params(axis='y', labelcolor=color_flux)
    ax2.set_yscale('log')
    
    plt.title("Daily Peak Solar X-ray Activity & Physical Flux (SoLEXS SDD2)", fontsize=14, fontweight='bold', pad=10)
    plt.tight_layout()
    
    bar_plot_path = os.path.join(root_dir, 'solexs_daily_peak_activity.png')
    plt.savefig(bar_plot_path)
    plt.close()
    print(f"Saved: {bar_plot_path}")
    
    # Export Event Catalog
    catalog_csv = os.path.join(root_dir, 'solexs_flare_candidate_catalog.csv')
    if not events_df.empty:
        export_events = events_df.copy()
        export_events['start_time'] = export_events['start_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        export_events['end_time'] = export_events['end_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        export_events['peak_time'] = export_events['peak_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        export_events = export_events.drop(columns=['peak_row_index'], errors='ignore')
        export_events.to_csv(catalog_csv, index=False)
        print(f"\nSaved flare candidate catalog to: {catalog_csv}")
        print("\nFull Flare Candidate Catalog (Top 25 events printed):")
        print("=" * 115)
        print(export_events.head(25).to_string(index=False))
        if len(export_events) > 25:
            print(f"... and {len(export_events)-25} more events in full CSV catalog ({catalog_csv})")
        print("=" * 115)
    else:
        empty_cat = pd.DataFrame(columns=['event_id', 'start_time', 'end_time', 'duration_sec', 'peak_time', 'peak_counts', 'peak_flux_wm2', 'goes_class', 'background_at_peak'])
        empty_cat.to_csv(catalog_csv, index=False)
        print(f"\nSaved empty flare candidate catalog (0 events found) to: {catalog_csv}")
        
    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT & PHYSICAL FLUX FORMULA")
    print("=" * 80)
    print(f"Total Rows Analyzed:          {len(df):,}")
    print(f"Date Range Covered:           {df['utc_time'].min()} to {df['utc_time'].max()}")
    print(f"Distinct Dates Present:       {len(daily_summary)} days")
    print(f"Total Timeline Gaps > 60s:    {len(gaps_df)}")
    print(f"Missing Calendar Dates:       {len(missing_dates)}")
    print(f"Flare Candidate Seconds:      {df['is_candidate'].sum():,} ({df['is_candidate'].mean()*100:.4f}%)")
    print(f"Discrete Candidate Events:    {len(events_df)}")
    print("-" * 80)
    print("PHYSICAL FLUX CONVERSION FORMULA:")
    print("  Energy Grid: E_i [keV] = 1.0 + (i + 0.5) * (29.0 / 340.0)  for i in 0..339")
    print("  Energy in Joules: E_i [J] = E_i [keV] * 1.60218e-16 J/keV")
    print("  Physical Flux (W/m²): F(t) = sum_i(COUNTS_i(t) * E_i [J]) / (EXPOSURE(t) * A_eff)")
    print("  where A_eff = 1.0e-5 m² (0.1 cm² nominal SDD aperture area).")
    print("=" * 80)
    print(f"CONFIRMATION: Successfully calculated physical flux and saved {len(events_df)} event(s) to catalog!")
    print("=" * 80)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]
    
    # Load dataset
    df, counts_2d = load_master_dataset(root_dir)
    
    # Step 3: Gap check
    gaps_df, missing_dates, present_dates = run_gap_analysis(df)
    
    # Step 4: Visualization
    plot_full_lightcurve(df, root_dir)
    plot_per_day_grid(df, present_dates, root_dir)
    
    # Step 5: Robust MAD Flare Detection
    events_df, df = detect_flare_candidates(df, root_dir)
    
    # Step 6: Per-event diagnostics
    generate_per_event_diagnostics(events_df, df, counts_2d, root_dir, max_plots=50)
    
    # Step 7: Reporting & Daily Summary
    generate_daily_summary_and_reporting(df, events_df, gaps_df, missing_dates, root_dir)

if __name__ == '__main__':
    main()
