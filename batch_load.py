import os
import sys
import numpy as np
import pandas as pd
from astropy.io import fits

def find_sdd2_pi_files(root_dir):
    """Find all SDD2 .pi files under root_dir, sorted chronologically by date in filename."""
    pi_files = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if 'SDD2' in f and f.endswith('.pi'):
                pi_files.append(os.path.join(root, f))
    # Sorting by filename sorts by date (20260704 -> 20260827)
    return sorted(pi_files, key=lambda x: os.path.basename(x))

def run_batch_loading(root_dir):
    print("=" * 60)
    print("STEP 2: BATCH LOADING SDD2 FITS DATA (MEMORY EFFICIENT)")
    print("=" * 60)
    
    pi_files = find_sdd2_pi_files(root_dir)
    print(f"Found {len(pi_files)} SDD2 .pi files under root directory.")
    
    # Pass 1: Quick scan to calculate total valid rows across all files
    print("\nScanning files to determine total valid row count...")
    file_info = []
    total_valid_rows = 0
    total_dropped_nan_rows = 0
    
    for idx, pf in enumerate(pi_files, start=1):
        rel_path = os.path.relpath(pf, root_dir)
        with fits.open(pf, memmap=True) as hdul:
            data = hdul[1].data
            counts = data['COUNTS'].byteswap().view(data['COUNTS'].dtype.newbyteorder('='))
            all_nan_mask = np.isnan(counts).all(axis=1)
            n_valid = int((~all_nan_mask).sum())
            n_dropped = int(all_nan_mask.sum())
            file_info.append({
                'filepath': pf,
                'rel_path': rel_path,
                'valid_rows': n_valid,
                'dropped_rows': n_dropped
            })
            total_valid_rows += n_valid
            total_dropped_nan_rows += n_dropped
            
    print(f"Total valid rows across all files: {total_valid_rows:,}")
    print(f"Total dropped all-NaN rows:       {total_dropped_nan_rows:,}")
    
    # Output file paths
    parquet_path = os.path.join(root_dir, 'solexs_master_timeseries.parquet')
    npy_path = os.path.join(root_dir, 'solexs_master_counts.npy')
    
    # Pre-allocate master .npy file on disk using memory-mapping (float32 for efficiency & precision)
    print(f"\nPre-allocating memory-mapped array at {npy_path} (shape: {total_valid_rows:,} x 340)...")
    master_counts_mm = np.lib.format.open_memmap(
        npy_path, mode='w+', dtype='float32', shape=(total_valid_rows, 340)
    )
    
    df_list = []
    current_idx = 0
    successfully_loaded = 0
    failed_files = []
    
    print("\nLoading binary tables into memory-mapped array & master dataframe...")
    for idx, info in enumerate(file_info, start=1):
        pf = info['filepath']
        rel_path = info['rel_path']
        n_valid = info['valid_rows']
        
        try:
            with fits.open(pf, memmap=True) as hdul:
                data = hdul[1].data
                
                # Byte-swap arrays
                tstart = data['TSTART'].byteswap().view(data['TSTART'].dtype.newbyteorder('='))
                telapse = data['TELAPSE'].byteswap().view(data['TELAPSE'].dtype.newbyteorder('='))
                exposure = data['EXPOSURE'].byteswap().view(data['EXPOSURE'].dtype.newbyteorder('='))
                counts = data['COUNTS'].byteswap().view(data['COUNTS'].dtype.newbyteorder('='))
                
                # Filter valid rows
                all_nan_mask = np.isnan(counts).all(axis=1)
                valid_mask = ~all_nan_mask
                
                tstart = tstart[valid_mask]
                telapse = telapse[valid_mask]
                exposure = exposure[valid_mask]
                counts_valid = counts[valid_mask].astype(np.float32)
                
                # Sum counts across 340 channels
                total_counts = np.nansum(counts_valid, axis=1)
                
                # Write counts slice directly to memmap
                master_counts_mm[current_idx : current_idx + n_valid, :] = counts_valid
                current_idx += n_valid
                
                df_file = pd.DataFrame({
                    'TSTART': tstart,
                    'TELAPSE': telapse,
                    'EXPOSURE': exposure,
                    'total_counts': total_counts
                })
                df_list.append(df_file)
                successfully_loaded += 1
                
                print(f"[{idx}/{len(pi_files)}] Loaded {rel_path} | Rows: {len(df_file):,}")
        except Exception as e:
            print(f"[{idx}/{len(pi_files)}] FAILED {rel_path}: {e}")
            failed_files.append((rel_path, str(e)))
            
    # Flush memmap to disk
    master_counts_mm.flush()
    del master_counts_mm
    
    print("\nConcatenating master timeseries DataFrame...")
    master_df = pd.concat(df_list, ignore_index=True)
    
    # If not sorted by TSTART, sort master_df and reorder npy array via memmap
    if not master_df['TSTART'].is_monotonic_increasing:
        print("Sorting dataset by TSTART...")
        sort_idx = np.argsort(master_df['TSTART'].values)
        master_df = master_df.iloc[sort_idx].reset_index(drop=True)
        
        print("Re-ordering memory-mapped counts array...")
        mm_read = np.load(npy_path, mmap_mode='r')
        tmp_npy_path = os.path.join(root_dir, 'solexs_master_counts_tmp.npy')
        mm_out = np.lib.format.open_memmap(tmp_npy_path, mode='w+', dtype='float32', shape=(total_valid_rows, 340))
        
        # Chunked copy to prevent memory spikes
        chunk_size = 200000
        for i in range(0, total_valid_rows, chunk_size):
            chunk_idx = sort_idx[i : i + chunk_size]
            mm_out[i : i + chunk_size, :] = mm_read[chunk_idx, :]
        mm_out.flush()
        del mm_read, mm_out
        os.remove(npy_path)
        os.rename(tmp_npy_path, npy_path)
    else:
        print("TSTART is already strictly monotonic increasing!")
        
    # Add UTC time column
    master_df['utc_time'] = pd.to_datetime(master_df['TSTART'], unit='s', utc=True)
    master_df = master_df[['TSTART', 'utc_time', 'TELAPSE', 'EXPOSURE', 'total_counts']]
    
    print(f"Saving master time series DataFrame to {parquet_path}...")
    master_df.to_parquet(parquet_path, index=False)
    
    # Dates present
    dates_present = sorted(master_df['utc_time'].dt.strftime('%Y-%m-%d').unique().tolist())
    min_date = master_df['utc_time'].min().strftime('%Y-%m-%d %H:%M:%S UTC')
    max_date = master_df['utc_time'].max().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Statistics on total_counts
    stats = master_df['total_counts'].describe()
    
    print("\n" + "=" * 60)
    print("BATCH LOADING SUMMARY")
    print("=" * 60)
    print(f"Total .pi files found:        {len(pi_files)}")
    print(f"Successfully loaded:          {successfully_loaded}")
    print(f"Failed files:                 {len(failed_files)}")
    print(f"Total rows in master dataset: {len(master_df):,}")
    print(f"Total dropped all-NaN rows:   {total_dropped_nan_rows:,}")
    print(f"Date range:                   {min_date} to {max_date}")
    print(f"Distinct calendar dates ({len(dates_present)}):")
    print("  " + ", ".join(dates_present[:10]) + (f" ... and {len(dates_present)-10} more" if len(dates_present) > 10 else ""))
    print("\nBasic Stats on total_counts:")
    print(stats.to_string())
    print("=" * 60)

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]
    run_batch_loading(root_dir)
