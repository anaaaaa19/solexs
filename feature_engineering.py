import os
import sys
import time
import numpy as np
import pandas as pd

def compute_features_and_labels(root_dir, horizon_minutes=15):
    print("=" * 60)
    print(f"PARTS B & C: FEATURE ENGINEERING & GAP-AWARE FORECAST TARGET (Horizon = {horizon_minutes}m)")
    print("=" * 60)
    
    t0 = time.time()
    parquet_path = os.path.join(root_dir, 'solexs_master_timeseries.parquet')
    npy_path = os.path.join(root_dir, 'solexs_master_counts.npy')
    cat_path = os.path.join(root_dir, 'solexs_flare_candidate_catalog.csv')
    daily_path = os.path.join(root_dir, 'solexs_daily_summary.csv')
    
    if not os.path.exists(parquet_path) or not os.path.exists(npy_path):
        raise FileNotFoundError("Master dataset files missing. Run batch_load.py first!")
        
    print(f"Loading master timeseries from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    df['utc_time'] = pd.to_datetime(df['utc_time'], utc=True)
    df['date_str'] = df['utc_time'].dt.strftime('%Y-%m-%d')
    N_total = len(df)
    print(f"Loaded {N_total:,} rows.")
    
    print(f"Loading 340-channel counts from {npy_path}...")
    counts_2d = np.load(npy_path, mmap_mode='r')
    
    # -------------------------------------------------------------
    # Step 1: Data Gap Segmentation (Do not bridge gaps > 300s)
    # -------------------------------------------------------------
    print("\nSegmenting continuous data streams (gap threshold = 300s)...")
    t_diff = df['TSTART'].diff()
    df['segment_id'] = (t_diff > 300.0).cumsum()
    n_segments = df['segment_id'].nunique()
    print(f"Identified {n_segments} continuous data segments.")
    
    # -------------------------------------------------------------
    # B1 & B2: Intensity, Background & Statistical Features
    # -------------------------------------------------------------
    print("\nComputing B1 & B2: Intensity, Statistical & Rate-of-Change features...")
    
    # Rolling background (30m window = 1800s centered)
    # Reuse centered time rolling median
    temp_df = df[['utc_time', 'total_counts']].set_index('utc_time')
    rolling_bg = temp_df['total_counts'].rolling('1800s', center=True, min_periods=30).median().values
    abs_diff = pd.Series(np.abs(temp_df['total_counts'].values - rolling_bg), index=temp_df.index)
    rolling_mad = abs_diff.rolling('1800s', center=True, min_periods=30).median().values
    
    df['background'] = rolling_bg
    df['excess'] = df['total_counts'] - df['background']
    df['robust_sigma'] = np.nan_to_num(rolling_mad * 1.4826, nan=1e-6)
    df['peak_to_bg_ratio'] = df['total_counts'] / (df['background'] + 1e-5)
    
    # Rolling statistics per segment (1m, 5m, 10m, 30m)
    # 60s, 300s, 600s, 1800s windows
    seg_grp = df.groupby('segment_id')['total_counts']
    
    df['rolling_mean_1m'] = seg_grp.transform(lambda x: x.rolling(60, min_periods=10).mean())
    df['rolling_std_1m']  = seg_grp.transform(lambda x: x.rolling(60, min_periods=10).std()).fillna(0.0)
    df['rolling_mean_5m'] = seg_grp.transform(lambda x: x.rolling(300, min_periods=30).mean())
    df['rolling_std_5m']  = seg_grp.transform(lambda x: x.rolling(300, min_periods=30).std()).fillna(0.0)
    df['rolling_mean_10m'] = seg_grp.transform(lambda x: x.rolling(600, min_periods=60).mean())
    df['rolling_std_10m']  = seg_grp.transform(lambda x: x.rolling(600, min_periods=60).std()).fillna(0.0)
    df['rolling_mean_30m'] = seg_grp.transform(lambda x: x.rolling(1800, min_periods=100).mean())
    df['rolling_std_30m']  = seg_grp.transform(lambda x: x.rolling(1800, min_periods=100).std()).fillna(0.0)
    
    # Rates of change (Derivatives within segment)
    df['d1_1m'] = seg_grp.transform(lambda x: x - x.shift(60)).fillna(0.0)
    df['d1_5m'] = seg_grp.transform(lambda x: x - x.shift(300)).fillna(0.0)
    d1_grp = df.groupby('segment_id')['d1_1m']
    df['d2_1m'] = d1_grp.transform(lambda x: x - x.shift(60)).fillna(0.0)
    
    # -------------------------------------------------------------
    # B3: Spectral Shape Features (from 340-channel array)
    # -------------------------------------------------------------
    print("\nComputing B3: 340-channel Spectral Shape features (Hardness & Centroid)...")
    low_band = np.zeros(N_total, dtype=np.float32)
    high_band = np.zeros(N_total, dtype=np.float32)
    centroid = np.zeros(N_total, dtype=np.float32)
    ch_indices = np.arange(340, dtype=np.float32)
    
    chunk_size = 500000
    for i in range(0, N_total, chunk_size):
        chunk = counts_2d[i : i + chunk_size]
        low_band[i : i + chunk_size] = chunk[:, :170].sum(axis=1)
        high_band[i : i + chunk_size] = chunk[:, 170:].sum(axis=1)
        tot = chunk.sum(axis=1)
        centroid[i : i + chunk_size] = np.dot(chunk, ch_indices) / (tot + 1e-5)
        
    df['hardness_ratio'] = (high_band + 1e-5) / (low_band + 1e-5)
    df['spectral_centroid'] = centroid
    
    hard_grp = df.groupby('segment_id')['hardness_ratio']
    df['hardness_trend_5m'] = hard_grp.transform(lambda x: x - x.shift(300)).fillna(0.0)
    df['hardness_trend_10m'] = hard_grp.transform(lambda x: x - x.shift(600)).fillna(0.0)
    
    # -------------------------------------------------------------
    # B4: Historical / Lag Features & Event History
    # -------------------------------------------------------------
    print("\nComputing B4: Historical & Event Lag features...")
    df['lag_counts_1m'] = seg_grp.transform(lambda x: x.shift(60)).fillna(df['total_counts'])
    df['lag_counts_5m'] = seg_grp.transform(lambda x: x.shift(300)).fillna(df['total_counts'])
    df['lag_counts_10m'] = seg_grp.transform(lambda x: x.shift(600)).fillna(df['total_counts'])
    
    # Event History from Catalog
    if os.path.exists(cat_path):
        cat = pd.read_csv(cat_path)
        cat['start_time'] = pd.to_datetime(cat['start_time'], utc=True)
        flare_starts = sorted(cat['start_time'].tolist())
    else:
        flare_starts = []
        
    print(f"Cross-referencing {len(flare_starts)} catalog flare start timestamps...")
    
    # Calculate time since last flare and counts in past 6h & 24h
    if flare_starts:
        flare_starts_sec = np.array([ts.timestamp() for ts in flare_starts])
        tstart_vals = df['TSTART'].values
        
        # Search position of current tstart in flare_starts
        idx_last = np.searchsorted(flare_starts_sec, tstart_vals, side='right') - 1
        
        time_since_last = np.where(
            idx_last >= 0,
            tstart_vals - flare_starts_sec[np.maximum(0, idx_last)],
            86400.0 * 30.0  # Default 30 days if no prior flare
        )
        
        idx_6h_start = np.searchsorted(flare_starts_sec, tstart_vals - 21600.0, side='left')
        count_6h = np.maximum(0, (idx_last + 1) - idx_6h_start)
        
        idx_24h_start = np.searchsorted(flare_starts_sec, tstart_vals - 86400.0, side='left')
        count_24h = np.maximum(0, (idx_last + 1) - idx_24h_start)
    else:
        time_since_last = np.full(N_total, 86400.0 * 30.0)
        count_6h = np.zeros(N_total, dtype=int)
        count_24h = np.zeros(N_total, dtype=int)
        
    df['time_since_last_flare_sec'] = time_since_last
    df['flare_count_past_6h'] = count_6h
    df['flare_count_past_24h'] = count_24h
    
    # -------------------------------------------------------------
    # B5: Data Quality Features & High-Dropout Days
    # -------------------------------------------------------------
    print("\nComputing B5: Data Quality & High-Dropout Day Flags...")
    if os.path.exists(daily_path):
        daily_df = pd.read_csv(daily_path)
        high_dropout_dates = set(daily_df[daily_df['n_seconds'] < 75000]['date_str'].tolist())
    else:
        high_dropout_dates = set()
        
    df['is_high_dropout_day'] = df['date_str'].isin(high_dropout_dates).astype(int)
    
    # Rolling valid fraction in recent 10m window (600s)
    # Check actual seconds elapsed over 600 rows vs 600
    tstart_shift600 = seg_grp.transform(lambda x: df.loc[x.index, 'TSTART'].shift(600))
    tstart_diff600 = df['TSTART'] - tstart_shift600
    df['rolling_valid_fraction_10m'] = np.where(
        tstart_diff600.isna(),
        1.0,
        np.clip(600.0 / (tstart_diff600 + 1e-5), 0.0, 1.0)
    )
    
    # -------------------------------------------------------------
    # B6: Reserved Placeholders for HEL1OS Dual-Instrument Fusion
    # -------------------------------------------------------------
    # Note: These columns are reserved schema placeholders for future
    # integration of HEL1OS Hard X-Ray (HXR) satellite observations.
    df['hel1os_hxr_to_sxr_lag_sec'] = np.nan
    df['hel1os_cumulative_hxr_flux'] = np.nan
    df['hel1os_cross_corr'] = np.nan
    
    # -------------------------------------------------------------
    # PART C: Binary Forecast Target Labeling
    # -------------------------------------------------------------
    print(f"\nComputing Part C Target Label: Flare start within next {horizon_minutes} minutes...")
    horizon_sec = horizon_minutes * 60.0
    
    if flare_starts:
        # Check if any flare start time falls in (tstart, tstart + horizon_sec]
        idx_next = np.searchsorted(flare_starts_sec, tstart_vals, side='right')
        has_next = idx_next < len(flare_starts_sec)
        next_flare_t = np.where(has_next, flare_starts_sec[np.minimum(len(flare_starts_sec)-1, idx_next)], np.inf)
        
        is_imminent = (next_flare_t > tstart_vals) & ((next_flare_t - tstart_vals) <= horizon_sec)
    else:
        is_imminent = np.zeros(N_total, dtype=bool)
        
    df['label_flare_imminent'] = is_imminent.astype(int)
    
    # Exclude time windows overlapping data gaps > 300s ahead from evaluation
    # Segment max TSTART
    seg_max_tstart = df.groupby('segment_id')['TSTART'].transform('max')
    df['valid_forecast_window'] = (seg_max_tstart - df['TSTART']) >= horizon_sec
    
    # Label summary report
    valid_mask = df['valid_forecast_window']
    pos_count = (df.loc[valid_mask, 'label_flare_imminent'] == 1).sum()
    neg_count = (df.loc[valid_mask, 'label_flare_imminent'] == 0).sum()
    total_valid = valid_mask.sum()
    pos_pct = (pos_count / total_valid) * 100 if total_valid > 0 else 0
    
    print("\n" + "=" * 60)
    print("FEATURE ENGINEERING & LABELING SUMMARY")
    print("=" * 60)
    print(f"Total Rows Processed:           {N_total:,}")
    print(f"Valid Evaluation Window Rows:  {total_valid:,} ({(total_valid/N_total)*100:.1f}%)")
    print(f"Negative Label Count (0):       {neg_count:,}")
    print(f"Positive Label Count (1):       {pos_count:,} ({pos_pct:.3f}% ratio)")
    print(f"Class Imbalance Ratio (0:1):   {neg_count / max(1, pos_count):.1f} : 1")
    print(f"Execution Time:                {time.time()-t0:.2f}s")
    print("=" * 60)
    
    out_matrix_path = os.path.join(root_dir, 'solexs_feature_matrix.parquet')
    print(f"\nSaving feature matrix to {out_matrix_path}...")
    df.to_parquet(out_matrix_path, index=False)
    print(f"Saved successfully!")
    return df

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]
    compute_features_and_labels(root_dir, horizon_minutes=15)
