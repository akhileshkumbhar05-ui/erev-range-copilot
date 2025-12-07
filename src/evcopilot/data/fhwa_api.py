from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import requests


# -------------------------------------------------------------------
# Config / paths
# -------------------------------------------------------------------

# Example VM-1 URL:
#   https://www.fhwa.dot.gov/policyinformation/statistics/2018/xls/vm1.xlsx
FHWA_VM1_URL_TEMPLATE = (
    "https://www.fhwa.dot.gov/policyinformation/statistics/{year}/xls/vm1.xlsx"
)

# fhwa_api.py is in: <project_root>/src/evcopilot/data/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = PROJECT_ROOT / "data" / "external"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class FHWAError(RuntimeError):
    """Errors raised when FHWA VM-1 data cannot be downloaded or parsed."""


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------

def _download_vm1_excel(year: int, force: bool = False) -> Path:
    """
    Download FHWA VM-1 Excel for a given year into data/external and return the path.
    """
    out_path = CACHE_DIR / f"fhwa_vm1_{year}.xlsx"
    if out_path.exists() and not force:
        return out_path

    url = FHWA_VM1_URL_TEMPLATE.format(year=year)
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise FHWAError(
            f"Could not download VM-1 for {year} from FHWA "
            f"(HTTP {resp.status_code}) at {url}"
        )
    out_path.write_bytes(resp.content)
    return out_path


def _read_vm1_with_dynamic_header(xlsx_path: Path) -> pd.DataFrame:
    """
    VM-1 puts the real header row somewhere below a block of title text.
    We scan for the row whose first cell is 'YEAR', then re-read using that row
    as the header.
    """
    raw = pd.read_excel(xlsx_path, sheet_name=0, header=None)

    header_row_candidates = raw.index[
        raw.iloc[:, 0].astype(str).str.strip().str.upper().eq("YEAR")
    ]
    if len(header_row_candidates) == 0:
        raise FHWAError(f"Could not find 'YEAR' header row in {xlsx_path}")
    header_row = int(header_row_candidates[0])

    df = pd.read_excel(xlsx_path, sheet_name=0, header=header_row)

    # Normalise column names (strip newlines and extra spaces)
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    return df


def _pick_col(df_year: pd.DataFrame, substr: str, year: int) -> str:
    """
    Find first column whose name contains the given substring (case-insensitive).
    Used for 2011–2022 VM-1 layout.
    """
    cand = [
        c for c in df_year.columns
        if substr.lower() in str(c).lower()
    ]
    if not cand:
        raise FHWAError(
            f"Could not find column containing '{substr}' in VM-1 for {year}.\n"
            f"Available columns: {list(df_year.columns)}"
        )
    return cand[0]


# -------------------------------------------------------------------
# Public API – vehicle-type breakdown (for dashboard)
# -------------------------------------------------------------------

def fetch_vm1_vehicle_type_totals(year: int) -> pd.Series:
    """
    Return national VMT totals (million vehicle-miles) by vehicle type for a
    given year (2011–2022; 2023+ not supported due to layout changes).

    Index in the returned Series:
        - 'All Light-Duty Vehicles'
        - 'Combination Trucks'
        - 'Single-Unit Trucks'
        - 'Bus'
        - 'Motorcycle'
    """
    if year >= 2023:
        raise FHWAError(
            "Vehicle-type breakdown is currently implemented only for years "
            "up to 2022 due to changes in FHWA VM-1 table layout in 2023+."
        )

    xlsx = _download_vm1_excel(year)
    df = _read_vm1_with_dynamic_header(xlsx)

    # Keep only numeric years (many VM-1 sheets have section headers etc)
    df = df.copy()
    df["YEAR_NUM"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df = df[df["YEAR_NUM"].notna()]
    df["YEAR_NUM"] = df["YEAR_NUM"].astype(int)

    df_year = df[df["YEAR_NUM"] == year]
    if df_year.empty:
        raise FHWAError(f"No rows for YEAR={year} in VM-1 file {xlsx}")

    # Typical column names (2011–2022) look like:
    #   LIGHT DUTY VEHICLES SHORT WB 2/
    #   LIGHT DUTY VEHICLES LONG WB 2/
    #   SINGLE-UNIT TRUCKS 3/
    #   COMBINATION TRUCKS
    #   BUSES
    #   MOTORCYCLES
    col_ldv_short = _pick_col(df_year, "LIGHT DUTY VEHICLES SHORT", year)
    col_ldv_long = _pick_col(df_year, "LIGHT DUTY VEHICLES LONG", year)
    col_mc = _pick_col(df_year, "MOTORCYCLE", year)
    col_bus = _pick_col(df_year, "BUS", year)
    col_su = _pick_col(df_year, "SINGLE-UNIT TRUCK", year)
    col_combo = _pick_col(df_year, "COMBINATION TRUCK", year)

    grouped = df_year.groupby("YEAR_NUM")[
        [col_ldv_short, col_ldv_long, col_mc, col_bus, col_su, col_combo]
    ].sum().iloc[0]

    out = pd.Series(
        {
            "All Light-Duty Vehicles": grouped[col_ldv_short] + grouped[col_ldv_long],
            "Combination Trucks": grouped[col_combo],
            "Single-Unit Trucks": grouped[col_su],
            "Bus": grouped[col_bus],
            "Motorcycle": grouped[col_mc],
        },
        name="VMT_million",
    )
    return out


def fetch_vm1_vehicle_type_panel(years: List[int]) -> pd.DataFrame:
    """
    Convenience function: return a long-format DataFrame with
    [year, vehicle_type, vmt_million] for multiple years.
    """
    records = []
    for y in years:
        s = fetch_vm1_vehicle_type_totals(y)
        for vtype, vmt_m in s.items():
            records.append(
                {
                    "year": y,
                    "vehicle_type": vtype,
                    "vmt_million": float(vmt_m),
                }
            )
    return pd.DataFrame.from_records(records)


# -------------------------------------------------------------------
# Public API – LDV total VMT for EREV calculations
# -------------------------------------------------------------------

def fetch_vm1_ldv_total_vmt_miles(year: int) -> float:
    """
    Return total LIGHT-DUTY vehicle VMT for a year in *miles*.

    For 2011–2022, this is computed from VM-1.
    For 2023, we return the constant used in the EREV paper (3.2628e12 miles)
    to keep the analysis aligned with published numbers and avoid depending
    on the newer VM-1 layout.
    """
    if year == 2023:
        # Constant used in your paper (total U.S. VMT 2023 in miles)
        return 3.2628e12

    # For earlier years, derive from VM-1 LDV columns
    s = fetch_vm1_vehicle_type_totals(year)
    return float(s["All Light-Duty Vehicles"] * 1e6)


def fetch_vm1_ldv_total_vmt_billion_miles(year: int) -> float:
    """
    Return total LIGHT-DUTY vehicle VMT for a year in *billion* miles.
    """
    return fetch_vm1_ldv_total_vmt_miles(year) / 1e9


# -------------------------------------------------------------------
# Smoke test
# -------------------------------------------------------------------

if __name__ == "__main__":
    test_year = 2018
    print(f"Checking FHWA VM-1 vehicle-type totals for {test_year}…")
    try:
        s = fetch_vm1_vehicle_type_totals(test_year)
        print(s)
    except FHWAError as e:
        print("Vehicle-type totals error:", e)

    test_year_ldv = 2023
    print(f"\nLDV total VMT (billion miles) for {test_year_ldv}:")
    print(fetch_vm1_ldv_total_vmt_billion_miles(test_year_ldv))
