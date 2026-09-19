"""
flare_pipeline.py
=================

Automated SoLEXS + HEL1OS solar flare nowcasting pipeline.

Pipeline:
1. Automatically extract ZIP files recursively.
2. Discover SoLEXS .pi files and HEL1OS CZT1 lightcurve FITS files.
3. Load SoLEXS and HEL1OS light curves.
4. Detect flare candidates independently using MAD.
5. Group and summarize flare events.
6. Fuse SoLEXS and HEL1OS detections (with leading-instrument + excess-flux stats).
7. Fetch GOES flare events from HEK.
8. Validate detected events against GOES (with GOES-class numeric flux parsing).
9. Compute aggregate TPR / FAR / lead-time / class-breakdown metrics.
10. Save final catalogues.

Outputs:
    <out_dir>/master_catalogue.csv
    <out_dir>/validated_master_catalogue.csv
    <out_dir>/goes_events.csv
    <out_dir>/run_log.csv
    <out_dir>/summary_metrics.csv
    <out_dir>/daily_data/<date>.parquet
"""

import os
import re
import zipfile
import warnings

import numpy as np
import pandas as pd

from astropy.io import fits
from sunpy.net import Fido, attrs as a


warnings.filterwarnings("ignore")


# ============================================================================
# CONFIGURATION
# ============================================================================

HEL1OS_FILE_NAME = "lightcurve_czt1.fits"

SOLEXS_NAME_RE = re.compile(
    r"AL1_SOLEXS_(\d{8})_SDD2_L1.*\.pi(?:\.gz)?$",
    re.IGNORECASE
)

HEL1OS_DATE_RE = re.compile(
    r"HLS_(\d{8})_\d{6}",
    re.IGNORECASE
)

# GOES class letter -> base flux multiplier (W/m^2), per NOAA convention
GOES_CLASS_BASE_FLUX = {
    "A": 1e-8,
    "B": 1e-7,
    "C": 1e-6,
    "M": 1e-5,
    "X": 1e-4,
}

GOES_CLASS_RE = re.compile(r"^([ABCMX])(\d+(?:\.\d+)?)$", re.IGNORECASE)


# ============================================================================
# GOES CLASS <-> FLUX HELPERS
# ============================================================================

def goes_class_to_flux(cls):
    """
    Convert a GOES class string like 'M2.3' or 'X1.3' into an
    approximate peak flux in W/m^2. Returns np.nan if unparseable.
    """

    if cls is None or (isinstance(cls, float) and np.isnan(cls)):
        return np.nan

    match = GOES_CLASS_RE.match(str(cls).strip())

    if not match:
        return np.nan

    letter = match.group(1).upper()
    magnitude = float(match.group(2))

    base = GOES_CLASS_BASE_FLUX.get(letter)

    if base is None:
        return np.nan

    return base * magnitude


def flux_to_goes_class(flux):
    """
    Convert an approximate flux (W/m^2) back into a GOES class string.
    Used to label detections that only have a SoLEXS/HEL1OS peak rate,
    not an official GOES class (best-effort, for display only).
    """

    if flux is None or (isinstance(flux, float) and np.isnan(flux)) or flux <= 0:
        return None

    order = ["X", "M", "C", "B", "A"]

    for letter in order:

        base = GOES_CLASS_BASE_FLUX[letter]

        if flux >= base:

            magnitude = flux / base

            return f"{letter}{magnitude:.1f}"

    return "A0.1"


def goes_class_rank(cls):
    """
    Numeric rank for sorting/plotting GOES classes on a log-like axis.
    A < B < C < M < X, larger magnitude = larger rank within a letter.
    """

    flux = goes_class_to_flux(cls)

    if np.isnan(flux):
        return np.nan

    return np.log10(flux)


# ============================================================================
# 1. AUTOMATICALLY EXTRACT ZIP FILES
# ============================================================================

def extract_zip_files(root_dir):
    """
    Recursively find and extract ZIP files.

    ZIP files are extracted into:

        <parent>/_extracted/<zip_name>/
    """

    extracted_count = 0

    print("\nChecking for ZIP files...")

    for dirpath, dirnames, filenames in os.walk(root_dir):

        # Do not recursively scan inside _extracted while looking for ZIP files
        dirnames[:] = [
            d for d in dirnames
            if d != "_extracted"
        ]

        for filename in filenames:

            if not filename.lower().endswith(".zip"):
                continue

            zip_path = os.path.join(
                dirpath,
                filename
            )

            zip_name = os.path.splitext(
                filename
            )[0]

            extract_dir = os.path.join(
                dirpath,
                "_extracted",
                zip_name
            )

            if os.path.exists(extract_dir):
                print(
                    f"Already extracted: {filename}"
                )
                continue

            print(
                f"Extracting: {filename}"
            )

            try:

                os.makedirs(
                    extract_dir,
                    exist_ok=True
                )

                with zipfile.ZipFile(
                    zip_path,
                    "r"
                ) as zip_ref:

                    zip_ref.extractall(
                        extract_dir
                    )

                extracted_count += 1

            except zipfile.BadZipFile:

                print(
                    f"WARNING: Invalid ZIP file: {filename}"
                )

            except Exception as exc:

                print(
                    f"WARNING: Could not extract "
                    f"{filename}: {exc}"
                )

    print(
        f"\nZIP extraction complete. "
        f"New ZIPs extracted: {extracted_count}"
    )


# ============================================================================
# 2. HELPER: EXTRACT HEL1OS DATE FROM PATH
# ============================================================================

def extract_hel1os_date(full_path):
    """
    Find HLS_YYYYMMDD_HHMMSS anywhere in the full path
    and return YYYY-MM-DD.
    """

    match = HEL1OS_DATE_RE.search(
        full_path.replace("\\", "/")
    )

    if not match:
        return None

    raw_date = match.group(1)

    return (
        f"{raw_date[0:4]}-"
        f"{raw_date[4:6]}-"
        f"{raw_date[6:8]}"
    )


# ============================================================================
# 3. DISCOVER SOLEXS + HEL1OS DATA
# ============================================================================

def discover_data(root_dir):
    """
    Recursively discover:

    SoLEXS:
        AL1_SOLEXS_YYYYMMDD_SDD2_L1*.pi

    HEL1OS:
        ONLY lightcurve_czt1.fits

    HEL1OS date is extracted from any HLS_YYYYMMDD_HHMMSS
    component found in the full path.
    """

    by_date = {}

    print(
        "\nSearching for SoLEXS and HEL1OS files..."
    )

    # Store normalized paths to avoid duplicates
    found_hel1os_paths = set()

    for dirpath, _dirnames, filenames in os.walk(root_dir):

        for fname in filenames:

            full_path = os.path.abspath(
                os.path.join(
                    dirpath,
                    fname
                )
            )

            # ---------------------------------------------------------------
            # SOLEXS
            # ---------------------------------------------------------------

            match = SOLEXS_NAME_RE.search(
                fname
            )

            if match:

                raw_date = match.group(1)

                date_str = (
                    f"{raw_date[0:4]}-"
                    f"{raw_date[4:6]}-"
                    f"{raw_date[6:8]}"
                )

                by_date.setdefault(
                    date_str,
                    {
                        "solexs": None,
                        "hel1os": []
                    }
                )

                # Keep first discovered SoLEXS file
                if by_date[date_str]["solexs"] is None:

                    by_date[date_str]["solexs"] = (
                        full_path
                    )

                    print(
                        f"SoLEXS found: "
                        f"{date_str}"
                    )

                continue

            # ---------------------------------------------------------------
            # HEL1OS
            # ONLY CZT1
            # ---------------------------------------------------------------

            if fname.lower() != HEL1OS_FILE_NAME.lower():
                continue

            # Make sure this is inside a CZT directory
            path_parts = [
                part.lower()
                for part in os.path.normpath(
                    full_path
                ).split(os.sep)
            ]

            if "czt" not in path_parts:
                continue

            date_str = extract_hel1os_date(
                full_path
            )

            if date_str is None:

                print(
                    f"WARNING: Could not determine "
                    f"HEL1OS date from:\n{full_path}"
                )

                continue

            normalized_path = os.path.normcase(
                os.path.normpath(
                    full_path
                )
            )

            if normalized_path in found_hel1os_paths:
                continue

            found_hel1os_paths.add(
                normalized_path
            )

            by_date.setdefault(
                date_str,
                {
                    "solexs": None,
                    "hel1os": []
                }
            )

            by_date[date_str]["hel1os"].append(
                full_path
            )

            print(
                f"HEL1OS CZT1 found: "
                f"{date_str}\n"
                f"  {full_path}"
            )

    # Remove duplicate paths within each date
    for date_str in by_date:

        unique_paths = []

        seen = set()

        for path in by_date[date_str]["hel1os"]:

            normalized = os.path.normcase(
                os.path.normpath(path)
            )

            if normalized not in seen:

                seen.add(normalized)

                unique_paths.append(path)

        by_date[date_str]["hel1os"] = (
            unique_paths
        )

    print("\nDiscovery Summary:")

    for date_str, paths in sorted(
        by_date.items()
    ):

        print(
            f"{date_str} | "
            f"SoLEXS: "
            f"{'YES' if paths['solexs'] else 'NO'} | "
            f"HEL1OS CZT1 segments: "
            f"{len(paths['hel1os'])}"
        )

    return dict(
        sorted(
            by_date.items()
        )
    )


# ============================================================================
# 4. LOAD SOLEXS
# ============================================================================

def load_solexs_day(path, date_str):

    with fits.open(path) as hdul:

        data = hdul[1].data

        tstart = np.asarray(
            data["TSTART"],
            dtype=float
        )

        counts = np.asarray(
            data["COUNTS"],
            dtype=float
        )

        exposure = np.asarray(
            data["EXPOSURE"],
            dtype=float
        )

    exposure_safe = np.where(
        exposure > 0,
        exposure,
        np.nan
    )

    # If COUNTS is multidimensional, sum over energy channels
    if counts.ndim > 1:

        rate = (
            np.nansum(
                counts,
                axis=1
            )
            /
            exposure_safe
        )

    else:

        rate = (
            counts
            /
            exposure_safe
        )

    valid_time = tstart[
        np.isfinite(tstart)
    ]

    if len(valid_time) == 0:

        raise ValueError(
            f"No valid TSTART values in "
            f"{path}"
        )

    time_hours = (
        tstart - np.nanmin(tstart)
    ) / 3600.0

    df = pd.DataFrame(
        {
            "time_hours": time_hours,
            "rate": rate
        }
    )

    df["rate"] = pd.to_numeric(
        df["rate"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "time_hours",
            "rate"
        ]
    ).reset_index(
        drop=True
    )

    day_start = pd.Timestamp(
        date_str
    )

    df["isot"] = (
        day_start
        +
        pd.to_timedelta(
            df["time_hours"],
            unit="h"
        )
    )

    df["instrument"] = "SoLEXS"

    return df[
        [
            "isot",
            "rate",
            "instrument"
        ]
    ]


# ============================================================================
# 5. FIND USABLE HEL1OS FITS EXTENSION
# ============================================================================

def _pick_hel1os_extension(hdul):
    """
    Find the FITS extension containing time and count-rate data.

    Preferred combinations:
        ISOT + CTR
        TIME + CTR
        TIME + RATE
    """

    preferred_time_columns = [
        "ISOT",
        "TIME",
        "TIMEDEL"
    ]

    preferred_rate_columns = [
        "CTR",
        "RATE",
        "COUNTRATE",
        "COUNT_RATE"
    ]

    best_idx = None

    for idx, hdu in enumerate(hdul):

        if hdu.data is None:
            continue

        if not hasattr(
            hdu.data,
            "names"
        ):
            continue

        names = [
            name.upper()
            for name in hdu.data.names
        ]

        has_time = any(
            col in names
            for col in preferred_time_columns
        )

        has_rate = any(
            col in names
            for col in preferred_rate_columns
        )

        if has_time and has_rate:

            return idx

    # Fallback:
    # search for any extension with CTR column
    for idx, hdu in enumerate(hdul):

        if hdu.data is None:
            continue

        if not hasattr(
            hdu.data,
            "names"
        ):
            continue

        names = [
            name.upper()
            for name in hdu.data.names
        ]

        if "CTR" in names:

            best_idx = idx
            break

    if best_idx is None:

        raise ValueError(
            "Could not find a HEL1OS FITS extension "
            "containing time and count-rate columns."
        )

    return best_idx


# ============================================================================
# 6. LOAD ONE HEL1OS SEGMENT
# ============================================================================

def load_hel1os_segment(path):
    """
    Load one HEL1OS lightcurve_czt1.fits segment.
    """

    with fits.open(path) as hdul:

        idx = _pick_hel1os_extension(
            hdul
        )

        data = hdul[idx].data

        names = [
            name.upper()
            for name in data.names
        ]

        # ---------------------------------------------------------------
        # FIND TIME COLUMN
        # ---------------------------------------------------------------

        time_col = None

        for candidate in [
            "ISOT",
            "TIME"
        ]:

            if candidate in names:

                time_col = data.names[
                    names.index(candidate)
                ]

                break

        if time_col is None:

            raise ValueError(
                f"No supported time column found in "
                f"HEL1OS extension {idx}. "
                f"Available columns: {data.names}"
            )

        # ---------------------------------------------------------------
        # FIND RATE COLUMN
        # ---------------------------------------------------------------

        rate_col = None

        for candidate in [
            "CTR",
            "RATE",
            "COUNTRATE",
            "COUNT_RATE"
        ]:

            if candidate in names:

                rate_col = data.names[
                    names.index(candidate)
                ]

                break

        if rate_col is None:

            raise ValueError(
                f"No supported rate column found in "
                f"HEL1OS extension {idx}. "
                f"Available columns: {data.names}"
            )

        isot_values = data[
            time_col
        ]

        rate_values = data[
            rate_col
        ]

    df = pd.DataFrame(
        {
            "isot": isot_values,
            "rate": rate_values
        }
    )

    # Convert time
    df["isot"] = pd.to_datetime(
        df["isot"],
        errors="coerce",
        utc=False
    )

    # Convert rate
    df["rate"] = pd.to_numeric(
        df["rate"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "isot",
            "rate"
        ]
    )

    df = df.sort_values(
        "isot"
    ).reset_index(
        drop=True
    )

    df["instrument"] = "HEL1OS"

    print(
        f"Loaded HEL1OS: "
        f"{os.path.basename(path)} | "
        f"rows={len(df)} | "
        f"extension={idx}"
    )

    return df[
        [
            "isot",
            "rate",
            "instrument"
        ]
    ]


# ============================================================================
# 7. LOAD ALL HEL1OS SEGMENTS FOR ONE DAY
# ============================================================================

def load_hel1os_day(paths):

    frames = []

    for path in paths:

        try:

            segment = load_hel1os_segment(
                path
            )

            if not segment.empty:

                frames.append(
                    segment
                )

        except Exception as exc:

            print(
                f"WARNING: HEL1OS segment failed:\n"
                f"{path}\n"
                f"Reason: {exc}"
            )

    if not frames:

        return pd.DataFrame(
            columns=[
                "isot",
                "rate",
                "instrument"
            ]
        )

    df = pd.concat(
        frames,
        ignore_index=True
    )

    # Remove duplicate timestamps
    df = df.sort_values(
        "isot"
    )

    df = df.drop_duplicates(
        subset=[
            "isot"
        ],
        keep="first"
    ).reset_index(
        drop=True
    )

    print(
        f"HEL1OS combined rows: "
        f"{len(df)}"
    )

    return df


# ============================================================================
# 8. MAD FLARE DETECTOR
# ============================================================================

def flag_flares_mad(
    df,
    rate_col="rate",
    window=300,
    k=5,
    min_periods=30,
    noise_floor=1e-9
):

    if df.empty:

        empty = pd.Series(
            False,
            index=df.index
        )

        nan_series = pd.Series(
            np.nan,
            index=df.index
        )

        return (
            empty,
            nan_series,
            nan_series
        )

    rate = pd.to_numeric(
        df[rate_col],
        errors="coerce"
    )

    baseline = rate.rolling(
        window=window,
        center=False,
        min_periods=min_periods
    ).median()

    mad = rate.rolling(
        window=window,
        center=False,
        min_periods=min_periods
    ).apply(
        lambda x: np.median(
            np.abs(
                x - np.median(x)
            )
        ),
        raw=True
    )

    scaled_mad = (
        mad * 1.4826
    ).clip(
        lower=noise_floor
    )

    threshold = (
        baseline
        +
        k * scaled_mad
    )

    is_flare = (
        rate > threshold
    )

    is_flare = is_flare.fillna(
        False
    )

    return (
        is_flare,
        baseline,
        threshold
    )


# ============================================================================
# 9. GROUP FLARE EVENTS
# ============================================================================

def group_flare_events(
    df,
    time_col="isot",
    flag_col="is_flare",
    max_gap_seconds=10,
    min_points=5
):

    if df.empty:

        return pd.DataFrame()

    events = df[
        df[flag_col] == True
    ].copy()

    if events.empty:

        return events

    events["time"] = pd.to_datetime(
        events[time_col],
        errors="coerce"
    )

    events = events.dropna(
        subset=[
            "time"
        ]
    )

    events = events.sort_values(
        "time"
    ).reset_index(
        drop=True
    )

    events["gap"] = (
        events["time"]
        .diff()
        .dt.total_seconds()
    )

    events["new_event"] = (
        events["gap"].isna()
        |
        (
            events["gap"]
            >
            max_gap_seconds
        )
    )

    events["event_id"] = (
        events["new_event"]
        .cumsum()
    )

    sizes = (
        events
        .groupby(
            "event_id"
        )
        .size()
    )

    valid_ids = sizes[
        sizes >= min_points
    ].index

    return events[
        events["event_id"].isin(
            valid_ids
        )
    ].copy()


# ============================================================================
# 10. SUMMARIZE EVENTS (with local background + excess stats)
# ============================================================================

def summarize_events(events, full_df=None, background_lookback_seconds=600):
    """
    events: output of group_flare_events (only flagged rows)
    full_df: the complete (unflagged) light curve for this instrument/day,
             used to estimate a pre-flare background level so we can compute
             excess flux and a peak/background ratio. Optional - if omitted,
             background/excess columns are left as NaN.
    """

    columns = [
        "event_id",
        "start_time",
        "peak_time",
        "peak_rate",
        "end_time",
        "duration_seconds",
        "flagged_samples",
        "background_rate",
        "excess_rate",
        "peak_to_background_ratio",
    ]

    if events.empty:

        return pd.DataFrame(
            columns=columns
        )

    rows = []

    for event_id, group in events.groupby(
        "event_id"
    ):

        start_time = group[
            "time"
        ].min()

        end_time = group[
            "time"
        ].max()

        peak_index = group[
            "rate"
        ].idxmax()

        peak_row = group.loc[
            peak_index
        ]

        background_rate = np.nan

        if full_df is not None and not full_df.empty and "isot" in full_df.columns:

            lookback_start = start_time - pd.Timedelta(seconds=background_lookback_seconds)

            pre_window = full_df[
                (full_df["isot"] >= lookback_start)
                & (full_df["isot"] < start_time)
            ]

            if not pre_window.empty:

                background_rate = pre_window["rate"].median()

        excess_rate = np.nan
        ratio = np.nan

        if not np.isnan(background_rate) and background_rate > 0:

            excess_rate = peak_row["rate"] - background_rate
            ratio = peak_row["rate"] / background_rate

        rows.append(
            {
                "event_id": event_id,
                "start_time": start_time,
                "peak_time": peak_row["time"],
                "peak_rate": peak_row["rate"],
                "end_time": end_time,
                "duration_seconds": (
                    end_time - start_time
                ).total_seconds(),
                "flagged_samples": len(group),
                "background_rate": background_rate,
                "excess_rate": excess_rate,
                "peak_to_background_ratio": ratio,
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns
    )


# ============================================================================
# 11. FUSE SOLEXS + HEL1OS (with leading-instrument + estimated class)
# ============================================================================

def fuse_catalogues(
    solexs_summary,
    hel1os_summary,
    match_window_minutes=15
):

    columns = [
        "solexs_start",
        "solexs_peak_time",
        "solexs_peak_rate",
        "solexs_end",
        "solexs_peak_to_background_ratio",
        "hel1os_peak_time",
        "hel1os_peak_rate",
        "hel1os_peak_to_background_ratio",
        "lead_time_minutes",
        "leading_instrument",
        "confirmation",
        "estimated_class",
    ]

    if solexs_summary.empty:

        return pd.DataFrame(
            columns=columns
        )

    fused = []

    solexs_summary = solexs_summary.copy()
    hel1os_summary = hel1os_summary.copy()

    solexs_summary["peak_time"] = pd.to_datetime(
        solexs_summary["peak_time"],
        errors="coerce"
    )

    if not hel1os_summary.empty:

        hel1os_summary["peak_time"] = pd.to_datetime(
            hel1os_summary["peak_time"],
            errors="coerce"
        )

    claimed_hel1os_ids = set()

    for _, s_row in solexs_summary.iterrows():

        s_peak = s_row[
            "peak_time"
        ]

        if pd.isna(s_peak):
            continue

        hel1os_peak_time = pd.NaT
        hel1os_peak_rate = np.nan
        hel1os_ratio = np.nan
        lead_time = np.nan
        leading_instrument = None
        confirmation = "SoLEXS-only"

        if not hel1os_summary.empty:

            window_start = (
                s_peak
                -
                pd.Timedelta(
                    minutes=match_window_minutes
                )
            )

            window_end = (
                s_peak
                +
                pd.Timedelta(
                    minutes=match_window_minutes
                )
            )

            matches = hel1os_summary[
                (
                    hel1os_summary["peak_time"]
                    >= window_start
                )
                &
                (
                    hel1os_summary["peak_time"]
                    <= window_end
                )
                &
                (
                    ~hel1os_summary["event_id"].isin(
                        claimed_hel1os_ids
                    )
                )
            ].copy()

            if not matches.empty:

                matches["time_difference"] = (
                    s_peak
                    -
                    matches["peak_time"]
                ).abs()

                h_row = matches.sort_values(
                    "time_difference"
                ).iloc[0]

                claimed_hel1os_ids.add(
                    h_row["event_id"]
                )

                hel1os_peak_time = h_row[
                    "peak_time"
                ]

                hel1os_peak_rate = h_row[
                    "peak_rate"
                ]

                hel1os_ratio = h_row.get(
                    "peak_to_background_ratio",
                    np.nan
                )

                lead_time = (
                    s_peak
                    -
                    hel1os_peak_time
                ).total_seconds() / 60.0

                confirmation = "Confirmed"

                # Positive lead_time -> HEL1OS peaked first (Neupert-consistent)
                # Negative lead_time -> SoLEXS peaked first / simultaneous
                leading_instrument = "HEL1OS" if lead_time > 0 else "SoLEXS"

        # Best-effort class estimate from SoLEXS peak rate isn't physically
        # calibrated to GOES flux, so we don't fabricate a class here.
        # This is filled in later once GOES validation supplies matched_goes_class,
        # or left None for unmatched events.
        estimated_class = None

        fused.append(
            {
                "solexs_start":
                    s_row["start_time"],

                "solexs_peak_time":
                    s_peak,

                "solexs_peak_rate":
                    s_row["peak_rate"],

                "solexs_end":
                    s_row["end_time"],

                "solexs_peak_to_background_ratio":
                    s_row.get("peak_to_background_ratio", np.nan),

                "hel1os_peak_time":
                    hel1os_peak_time,

                "hel1os_peak_rate":
                    hel1os_peak_rate,

                "hel1os_peak_to_background_ratio":
                    hel1os_ratio,

                "lead_time_minutes":
                    lead_time,

                "leading_instrument":
                    leading_instrument,

                "confirmation":
                    confirmation,

                "estimated_class":
                    estimated_class,
            }
        )

    return pd.DataFrame(
        fused,
        columns=columns
    )


# ============================================================================
# 12. FETCH GOES EVENTS
# ============================================================================

def fetch_goes_events(date_str):
    """
    Query HEK for GOES flare events on a given date.

    Returns a 3-tuple:
        (goes_df, status, message)

    status is one of:
        "ok"    - events were found and parsed successfully
        "empty" - the query succeeded but returned no usable events
        "error" - the query itself failed (network, HEK, parsing, etc.)

    message is a human-readable explanation, empty string on "ok".
    """

    columns = [
        "goes_start",
        "goes_peak",
        "goes_end",
        "goes_class",
        "goes_flux",
        "goes_class_rank",
    ]

    start_time = pd.Timestamp(
        date_str
    )

    end_time = (
        start_time
        +
        pd.Timedelta(
            days=1
        )
    )

    try:

        result = Fido.search(

            a.Time(
                start_time.isoformat(),
                end_time.isoformat()
            ),

            a.hek.EventType("FL"),

            a.hek.OBS.Observatory
            ==
            "GOES"
        )

        hek_table = result["hek"]

        if len(hek_table) == 0:

            message = (
                f"HEK returned no GOES flare events for {date_str}. "
                f"This is often normal for quiet days, but can also mean "
                f"the event hasn't been catalogued yet."
            )

            print(message)

            return (
                pd.DataFrame(columns=columns),
                "empty",
                message
            )

        goes_df = pd.DataFrame(
            {
                "goes_start": [
                    str(t)
                    for t in hek_table[
                        "event_starttime"
                    ]
                ],

                "goes_peak": [
                    str(t)
                    for t in hek_table[
                        "event_peaktime"
                    ]
                ],

                "goes_end": [
                    str(t)
                    for t in hek_table[
                        "event_endtime"
                    ]
                ],

                "goes_class": [
                    str(c)
                    for c in hek_table[
                        "fl_goescls"
                    ]
                ]
            }
        )

        for col in [
            "goes_start",
            "goes_peak",
            "goes_end"
        ]:

            goes_df[col] = pd.to_datetime(
                goes_df[col],
                errors="coerce"
            )

        goes_df = goes_df.dropna(
            subset=[
                "goes_peak"
            ]
        )

        goes_df["goes_flux"] = goes_df["goes_class"].apply(goes_class_to_flux)
        goes_df["goes_class_rank"] = goes_df["goes_class"].apply(goes_class_rank)

        goes_df = goes_df.sort_values(
            "goes_peak"
        ).reset_index(
            drop=True
        )

        if goes_df.empty:

            message = (
                f"HEK returned {len(hek_table)} row(s) for {date_str}, "
                f"but none had a parseable goes_peak timestamp."
            )

            print(message)

            return (
                goes_df,
                "empty",
                message
            )

        return (
            goes_df,
            "ok",
            ""
        )

    except Exception as exc:

        message = f"GOES/HEK fetch failed for {date_str}: {exc}"

        print(
            message
        )

        return (
            pd.DataFrame(columns=columns),
            "error",
            message
        )


# ============================================================================
# 13. VALIDATE AGAINST GOES
# ============================================================================

def validate_against_goes(
    master_catalogue,
    goes_df,
    match_window_minutes=10
):

    master = master_catalogue.copy()

    master["matched_goes_class"] = None
    master["matched_goes_flux"] = np.nan
    master["matched_goes_peak"] = pd.NaT
    master["time_difference_seconds"] = np.nan
    master["is_true_positive"] = False

    if master.empty:

        return master

    master["solexs_peak_time"] = pd.to_datetime(
        master["solexs_peak_time"],
        errors="coerce"
    )

    if goes_df.empty:

        return master

    goes = goes_df.copy()

    goes["goes_peak"] = pd.to_datetime(
        goes["goes_peak"],
        errors="coerce"
    )

    goes = goes.dropna(
        subset=[
            "goes_peak"
        ]
    ).reset_index(
        drop=True
    )

    if "goes_flux" not in goes.columns:
        goes["goes_flux"] = goes["goes_class"].apply(goes_class_to_flux)

    claimed_goes_ids = set()

    for master_index, row in master.iterrows():

        detected_peak = row[
            "solexs_peak_time"
        ]

        if pd.isna(detected_peak):
            continue

        window_start = (
            detected_peak
            -
            pd.Timedelta(
                minutes=match_window_minutes
            )
        )

        window_end = (
            detected_peak
            +
            pd.Timedelta(
                minutes=match_window_minutes
            )
        )

        candidates = goes[
            (
                goes["goes_peak"]
                >= window_start
            )
            &
            (
                goes["goes_peak"]
                <= window_end
            )
            &
            (
                ~goes.index.isin(
                    claimed_goes_ids
                )
            )
        ].copy()

        if candidates.empty:
            continue

        candidates["time_difference"] = (
            detected_peak
            -
            candidates["goes_peak"]
        ).abs()

        best_match = candidates.sort_values(
            "time_difference"
        ).iloc[0]

        best_id = best_match.name

        claimed_goes_ids.add(
            best_id
        )

        difference_seconds = abs(
            (
                detected_peak
                -
                best_match["goes_peak"]
            ).total_seconds()
        )

        master.loc[
            master_index,
            "matched_goes_class"
        ] = str(
            best_match["goes_class"]
        )

        master.loc[
            master_index,
            "matched_goes_flux"
        ] = best_match.get("goes_flux", np.nan)

        master.loc[
            master_index,
            "matched_goes_peak"
        ] = best_match[
            "goes_peak"
        ]

        master.loc[
            master_index,
            "time_difference_seconds"
        ] = difference_seconds

        master.loc[
            master_index,
            "is_true_positive"
        ] = True

        # Fill in estimated_class with the real matched GOES class now that we have it
        master.loc[
            master_index,
            "estimated_class"
        ] = str(best_match["goes_class"])

    return master


# ============================================================================
# 14. AGGREGATE METRICS (TPR / FAR / lead time / class breakdown)
# ============================================================================

def compute_summary_metrics(master_catalogue, goes_catalogue):
    """
    Compute headline evaluation-criteria metrics across the full
    (possibly multi-day) master catalogue:

        - Total detections
        - True positives / false positives
        - Total real GOES flares available for comparison
        - False negatives (GOES flares with no matching detection)
        - TPR, FAR
        - Lead time stats (mean/median/min/max) for Confirmed events
        - Per-GOES-class breakdown (how many of each class were caught)
    """

    metrics = {}

    total_detections = len(master_catalogue)
    metrics["total_detections"] = total_detections

    if total_detections == 0 or "is_true_positive" not in master_catalogue.columns:

        metrics.update({
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "tpr_percent": np.nan,
            "far_percent": np.nan,
            "mean_lead_time_minutes": np.nan,
            "median_lead_time_minutes": np.nan,
            "min_lead_time_minutes": np.nan,
            "max_lead_time_minutes": np.nan,
            "confirmed_events": 0,
        })

        return pd.DataFrame([metrics]), pd.DataFrame()

    tp = int(master_catalogue["is_true_positive"].fillna(False).sum())
    fp = total_detections - tp

    total_goes_flares = len(goes_catalogue) if goes_catalogue is not None else 0
    fn = max(total_goes_flares - tp, 0)

    tpr = (tp / total_goes_flares * 100) if total_goes_flares > 0 else np.nan
    far = (fp / total_detections * 100) if total_detections > 0 else np.nan

    confirmed = master_catalogue[master_catalogue["confirmation"] == "Confirmed"]
    lead_times = confirmed["lead_time_minutes"].dropna()

    metrics.update({
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "total_goes_flares": total_goes_flares,
        "tpr_percent": tpr,
        "far_percent": far,
        "mean_lead_time_minutes": lead_times.mean() if not lead_times.empty else np.nan,
        "median_lead_time_minutes": lead_times.median() if not lead_times.empty else np.nan,
        "min_lead_time_minutes": lead_times.min() if not lead_times.empty else np.nan,
        "max_lead_time_minutes": lead_times.max() if not lead_times.empty else np.nan,
        "confirmed_events": len(confirmed),
    })

    # Per-class breakdown: of the GOES flares we know about, how many
    # in each letter-class did we detect (is_true_positive)?
    class_breakdown = pd.DataFrame()

    if goes_catalogue is not None and not goes_catalogue.empty and "goes_class" in goes_catalogue.columns:

        goes_copy = goes_catalogue.copy()

        goes_copy["letter"] = goes_copy["goes_class"].astype(str).str[0].str.upper()

        matched_classes = master_catalogue.loc[
            master_catalogue["is_true_positive"] == True,
            "matched_goes_class"
        ].dropna().astype(str)

        matched_letters = matched_classes.str[0].str.upper()

        rows = []

        for letter in ["A", "B", "C", "M", "X"]:

            total_letter = int((goes_copy["letter"] == letter).sum())
            caught_letter = int((matched_letters == letter).sum())

            if total_letter == 0:
                continue

            rows.append({
                "goes_letter_class": letter,
                "total_flares": total_letter,
                "detected_flares": caught_letter,
                "detection_rate_percent": (caught_letter / total_letter * 100) if total_letter > 0 else np.nan,
            })

        class_breakdown = pd.DataFrame(rows)

    return pd.DataFrame([metrics]), class_breakdown


# ============================================================================
# 15. PROCESS ONE DAY
# ============================================================================

def process_day(
    date_str,
    solexs_path,
    hel1os_paths,
    mad_window=300,
    mad_k=5,
    goes_match_window=10
):

    result = {
        "date": date_str,
        "master": pd.DataFrame(),
        "goes": pd.DataFrame(),
        "combined": pd.DataFrame(),
        "status": "ok",
        "message": "",
        "goes_status": "not_run",
        "goes_message": ""
    }

    # -----------------------------------------------------------------------
    # CHECK DATA
    # -----------------------------------------------------------------------

    if solexs_path is None:

        result["status"] = "skipped"

        result["message"] = (
            f"Missing SoLEXS data "
            f"for {date_str}"
        )

        return result

    if not hel1os_paths:

        result["status"] = "skipped"

        result["message"] = (
            f"Missing HEL1OS CZT1 data "
            f"for {date_str}"
        )

        return result

    try:

        print(
            f"\nProcessing date: {date_str}"
        )

        # -------------------------------------------------------------------
        # LOAD DATA
        # -------------------------------------------------------------------

        df_solexs = load_solexs_day(
            solexs_path,
            date_str
        )

        print(
            f"SoLEXS rows: "
            f"{len(df_solexs)}"
        )

        df_hel1os = load_hel1os_day(
            hel1os_paths
        )

        print(
            f"HEL1OS rows: "
            f"{len(df_hel1os)}"
        )

        if df_hel1os.empty:

            raise ValueError(
                "HEL1OS CZT1 files were discovered "
                "but no valid data could be loaded."
            )

        # -------------------------------------------------------------------
        # CLEAN RATES
        # -------------------------------------------------------------------

        df_solexs["rate"] = pd.to_numeric(
            df_solexs["rate"],
            errors="coerce"
        )

        df_solexs = df_solexs.dropna(
            subset=[
                "rate"
            ]
        )

        df_hel1os["rate"] = pd.to_numeric(
            df_hel1os["rate"],
            errors="coerce"
        )

        df_hel1os = df_hel1os.dropna(
            subset=[
                "rate"
            ]
        )

        # Keep positive HEL1OS rates
        df_hel1os_positive = df_hel1os[
            df_hel1os["rate"] > 0
        ].copy()

        # -------------------------------------------------------------------
        # DETECT SOLEXS FLARES
        # -------------------------------------------------------------------

        (
            df_solexs["is_flare"],
            _,
            _
        ) = flag_flares_mad(

            df_solexs,

            window=mad_window,

            k=mad_k
        )

        # -------------------------------------------------------------------
        # DETECT HEL1OS FLARES
        # -------------------------------------------------------------------

        (
            df_hel1os_positive["is_flare"],
            _,
            _
        ) = flag_flares_mad(

            df_hel1os_positive,

            window=mad_window,

            k=mad_k
        )

        print(
            f"SoLEXS flagged samples: "
            f"{df_solexs['is_flare'].sum()}"
        )

        print(
            f"HEL1OS flagged samples: "
            f"{df_hel1os_positive['is_flare'].sum()}"
        )

        # -------------------------------------------------------------------
        # GROUP EVENTS
        # -------------------------------------------------------------------

        solexs_events = group_flare_events(

            df_solexs,

            max_gap_seconds=10,

            min_points=5
        )

        hel1os_events = group_flare_events(

            df_hel1os_positive,

            max_gap_seconds=15,

            min_points=5
        )

        # -------------------------------------------------------------------
        # SUMMARIZE EVENTS (with background/excess-flux stats)
        # -------------------------------------------------------------------

        solexs_summary = summarize_events(
            solexs_events,
            full_df=df_solexs
        )

        hel1os_summary = summarize_events(
            hel1os_events,
            full_df=df_hel1os_positive
        )

        print(
            f"SoLEXS events: "
            f"{len(solexs_summary)}"
        )

        print(
            f"HEL1OS events: "
            f"{len(hel1os_summary)}"
        )

        # -------------------------------------------------------------------
        # FUSE
        # -------------------------------------------------------------------

        master = fuse_catalogues(

            solexs_summary,

            hel1os_summary,

            match_window_minutes=15
        )

        # -------------------------------------------------------------------
        # FETCH GOES
        # -------------------------------------------------------------------

        goes_df, goes_status, goes_message = fetch_goes_events(
            date_str
        )

        result["goes_status"] = goes_status
        result["goes_message"] = goes_message

        # -------------------------------------------------------------------
        # VALIDATE WITH GOES
        # -------------------------------------------------------------------

        master = validate_against_goes(

            master,

            goes_df,

            match_window_minutes=goes_match_window
        )

        master["date"] = date_str

        result["master"] = master
        result["goes"] = goes_df

        # -------------------------------------------------------------------
        # COMBINED LIGHT CURVE
        # -------------------------------------------------------------------

        combined = pd.concat(

            [

                df_solexs[
                    [
                        "isot",
                        "rate",
                        "instrument",
                        "is_flare"
                    ]
                ],

                df_hel1os_positive[
                    [
                        "isot",
                        "rate",
                        "instrument",
                        "is_flare"
                    ]
                ]

            ],

            ignore_index=True

        ).sort_values(

            "isot"

        ).reset_index(

            drop=True
        )

        result["combined"] = combined

    except Exception as exc:

        result["status"] = "error"

        result["message"] = (
            f"{date_str}: {exc}"
        )

        print(
            f"ERROR processing "
            f"{date_str}: {exc}"
        )

    return result


# ============================================================================
# 16. RUN COMPLETE PIPELINE
# ============================================================================

def run_pipeline(
    root_dir,
    out_dir,
    mad_window=300,
    mad_k=5,
    goes_match_window=10,
    progress_callback=None
):

    # -----------------------------------------------------------------------
    # CREATE OUTPUT FOLDERS
    # -----------------------------------------------------------------------

    os.makedirs(
        out_dir,
        exist_ok=True
    )

    daily_dir = os.path.join(
        out_dir,
        "daily_data"
    )

    os.makedirs(
        daily_dir,
        exist_ok=True
    )

    # -----------------------------------------------------------------------
    # STEP 1: EXTRACT ZIP FILES
    # -----------------------------------------------------------------------

    extract_zip_files(
        root_dir
    )

    # -----------------------------------------------------------------------
    # STEP 2: DISCOVER DATA
    # -----------------------------------------------------------------------

    by_date = discover_data(
        root_dir
    )

    if not by_date:

        raise FileNotFoundError(
            f"No SoLEXS/HEL1OS files found under "
            f"{root_dir}"
        )

    all_master = []
    all_goes = []
    log_rows = []

    dates = list(
        by_date.keys()
    )

    print(
        f"\nTotal dates discovered: "
        f"{len(dates)}"
    )

    # -----------------------------------------------------------------------
    # PROCESS EVERY DATE
    # -----------------------------------------------------------------------

    for i, date_str in enumerate(
        dates
    ):

        paths = by_date[
            date_str
        ]

        result = process_day(

            date_str,

            paths["solexs"],

            paths["hel1os"],

            mad_window=mad_window,

            mad_k=mad_k,

            goes_match_window=goes_match_window
        )

        log_rows.append(
            {
                "date": date_str,
                "status": result["status"],
                "message": result["message"],
                "goes_status": result.get("goes_status", ""),
                "goes_message": result.get("goes_message", "")
            }
        )

        if result["status"] == "ok":

            if not result["master"].empty:

                all_master.append(
                    result["master"]
                )

            if not result["goes"].empty:

                goes_copy = result[
                    "goes"
                ].copy()

                goes_copy["date"] = (
                    date_str
                )

                all_goes.append(
                    goes_copy
                )

            if not result["combined"].empty:

                daily_path = os.path.join(
                    daily_dir,
                    f"{date_str}.parquet"
                )

                try:

                    result["combined"].to_parquet(
                        daily_path,
                        index=False
                    )

                except Exception as exc:

                    print(
                        f"WARNING: Could not save "
                        f"Parquet for {date_str}: {exc}"
                    )

        if progress_callback:

            progress_callback(

                i + 1,

                len(dates),

                date_str,

                result["status"]
            )

    # -----------------------------------------------------------------------
    # COMBINE MASTER CATALOGUE
    # -----------------------------------------------------------------------

    if all_master:

        master_catalogue = pd.concat(

            all_master,

            ignore_index=True
        )

    else:

        master_catalogue = pd.DataFrame()

    # -----------------------------------------------------------------------
    # COMBINE GOES EVENTS
    # -----------------------------------------------------------------------

    if all_goes:

        goes_catalogue = pd.concat(

            all_goes,

            ignore_index=True
        )

    else:

        goes_catalogue = pd.DataFrame()

    # -----------------------------------------------------------------------
    # VALIDATED CATALOGUE
    # -----------------------------------------------------------------------

    if (
        not master_catalogue.empty
        and
        "is_true_positive"
        in master_catalogue.columns
    ):

        validated_catalogue = master_catalogue[
            master_catalogue[
                "is_true_positive"
            ] == True
        ].copy()

    else:

        validated_catalogue = pd.DataFrame(
            columns=master_catalogue.columns
        )

    # -----------------------------------------------------------------------
    # AGGREGATE METRICS (TPR / FAR / lead time / class breakdown)
    # -----------------------------------------------------------------------

    summary_df, class_breakdown_df = compute_summary_metrics(
        master_catalogue,
        goes_catalogue
    )

    # -----------------------------------------------------------------------
    # SAVE OUTPUTS
    # -----------------------------------------------------------------------

    master_path = os.path.join(out_dir, "master_catalogue.csv")
    validated_path = os.path.join(out_dir, "validated_master_catalogue.csv")
    goes_path = os.path.join(out_dir, "goes_events.csv")
    log_path = os.path.join(out_dir, "run_log.csv")
    summary_path = os.path.join(out_dir, "summary_metrics.csv")
    class_breakdown_path = os.path.join(out_dir, "class_breakdown.csv")

    master_catalogue.to_csv(master_path, index=False)
    validated_catalogue.to_csv(validated_path, index=False)
    goes_catalogue.to_csv(goes_path, index=False)

    log_df = pd.DataFrame(log_rows)
    log_df.to_csv(log_path, index=False)

    summary_df.to_csv(summary_path, index=False)
    class_breakdown_df.to_csv(class_breakdown_path, index=False)

    # -----------------------------------------------------------------------
    # FINAL METRICS (console)
    # -----------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    if not summary_df.empty:

        row = summary_df.iloc[0]

        print(f"\nTotal Detected Events: {row['total_detections']}")
        print(f"True Positives: {row['true_positives']}")
        print(f"False Positives: {row['false_positives']}")
        print(f"False Negatives: {row.get('false_negatives', 'n/a')}")
        print(f"TPR: {row.get('tpr_percent', float('nan')):.1f}%")
        print(f"FAR: {row.get('far_percent', float('nan')):.1f}%")
        print(f"Mean Lead Time (Confirmed): {row.get('mean_lead_time_minutes', float('nan')):.2f} min")

    else:

        print("\nNo detected flare events found.")

    print(f"\nMaster catalogue:\n{master_path}")
    print(f"\nValidated catalogue:\n{validated_path}")
    print(f"\nGOES catalogue:\n{goes_path}")
    print(f"\nSummary metrics:\n{summary_path}")
    print(f"\nClass breakdown:\n{class_breakdown_path}")
    print(f"\nRun log:\n{log_path}")

    return (
        master_catalogue,
        goes_catalogue,
        log_df,
        summary_df,
        class_breakdown_df,
    )


# ============================================================================
# 17. COMMAND LINE RUNNER
# ============================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(

        description=(
            "Automated SoLEXS + HEL1OS CZT1 + "
            "GOES solar flare validation pipeline."
        )
    )

    parser.add_argument("--root", required=True, help="Folder containing ZIP or extracted SoLEXS and HEL1OS data")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument("--window", type=int, default=300, help="MAD rolling window")
    parser.add_argument("--k", type=float, default=5, help="MAD sensitivity")
    parser.add_argument("--goes_window", type=float, default=10, help="GOES matching window in minutes")

    args = parser.parse_args()

    def _print_progress(done, total, date_str, status):

        print(f"[{done}/{total}] {date_str}: {status}")

    catalogue, goes, log, summary, class_breakdown = run_pipeline(

        root_dir=args.root,
        out_dir=args.out,
        mad_window=args.window,
        mad_k=args.k,
        goes_match_window=args.goes_window,
        progress_callback=_print_progress
    )

    print("\nDone.")
    print(f"Detected flare events: {len(catalogue)}")