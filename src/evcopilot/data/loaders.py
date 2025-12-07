from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd

from evcopilot.model.vmt_bins import TripBin


def get_project_root() -> Path:
    """Return the project root directory.

    Assumes this file lives in src/evcopilot/data/loaders.py.
    """
    return Path(__file__).resolve().parents[3]


def get_raw_data_dir() -> Path:
    return get_project_root() / "data" / "raw"


def load_trip_bins_from_csv(csv_path: Path) -> List[TripBin]:
    """Load trip-distance bins from a CSV file.

    Expected columns:
        - bin_lower_miles : float, inclusive lower bound
        - bin_upper_miles : float, exclusive upper bound; may be blank/NaN for open-ended
        - share_of_trips  : float, fraction of trips in this bin (0–1), will be renormalised
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Trip-bin file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_cols = {"bin_lower_miles", "bin_upper_miles", "share_of_trips"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    bins: List[TripBin] = []
    for _, row in df.iterrows():
        lower = float(row["bin_lower_miles"])
        upper_val = row["bin_upper_miles"]
        upper = None if pd.isna(upper_val) else float(upper_val)
        share = float(row["share_of_trips"])
        bins.append(TripBin(lower=lower, upper=upper, share_of_trips=share))

    # Renormalise shares just in case they don't sum exactly to 1
    total_share = sum(b.share_of_trips for b in bins)
    if total_share <= 0:
        raise ValueError("Sum of share_of_trips must be > 0")
    for b in bins:
        b.share_of_trips /= total_share

    return bins
