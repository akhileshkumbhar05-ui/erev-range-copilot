# NOTE: Legacy script kept for reference; main entrypoint is run_full_pipeline.py.

from __future__ import annotations

from itertools import product
from pathlib import Path
import sys

import pandas as pd

# Wire up src/ to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.data.loaders import get_raw_data_dir, load_trip_bins_from_csv
from evcopilot.model.range_scenarios import compute_range_scenario
from evcopilot.model.vmt_bins import TripBin, compute_ev_share_for_range
from evcopilot.model.erev_calculations import run_erev_analysis

def main() -> None:
    # 1) Load trip bins from CSV
    raw_dir = get_raw_data_dir()
    bins_csv = raw_dir / "trip_bins_example.csv"
    trip_bins: list[TripBin] = load_trip_bins_from_csv(bins_csv)
    print(f"Loaded {len(trip_bins)} trip bins from {bins_csv}")

    # 2) Compute EV share vs range using these bins (charges_per_week=5, Average scenario)
    ranges = list(range(25, 151, 5))
    scenario_name = "Average"
    charges_per_week = 5

    rows = []
    for r in ranges:
        # Use *your* bins in the lower-level model
        ev_share_from_bins = compute_ev_share_for_range(r, bins=trip_bins)
        res = compute_range_scenario(
            range_miles=r,
            charges_per_week=charges_per_week,
            scenario_name=scenario_name,
        )

        rows.append(
            {
                "range_miles": r,
                "ev_share_from_bins": ev_share_from_bins,
                "ev_share_pipeline": res.ev_share,
                "co2_savings_tons": res.co2_savings_tons,
                "capex_per_ton_usd": res.capex_per_ton_usd,
            }
        )

    df = pd.DataFrame(rows)

    out_dir = PROJECT_ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "erev_range_results_example.csv"
    df.to_csv(out_path, index=False)

    print(f"Wrote {len(df)} rows to {out_path}")
    print(df.head())

        # 3) Run full EREV calculations pipeline (paper-equivalent)
    print("\nRunning full EREV calculations (erev_calculations.run_erev_analysis)...")
    df_erev = run_erev_analysis(save_csv=True)
    print("EREV results (first 5 rows):")
    print(df_erev.head())

if __name__ == "__main__":
    main()
