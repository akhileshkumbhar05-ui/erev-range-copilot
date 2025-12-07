from __future__ import annotations

from pathlib import Path
import sys
from itertools import product

import pandas as pd

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.model.range_scenarios import compute_range_scenario


def main() -> None:
    ranges = list(range(25, 151, 25))          # 25, 50, ..., 150
    charges_options = [2, 3, 5, 7]
    scenarios = ["Worst", "Average", "Best"]

    rows = []
    for r, c, s in product(ranges, charges_options, scenarios):
        res = compute_range_scenario(range_miles=r, charges_per_week=c, scenario_name=s)
        rows.append(
            {
                "range_miles": res.range_miles,
                "charges_per_week": res.charges_per_week,
                "scenario": res.scenario_name,
                "ev_share": res.ev_share,
                "ev_vmt": res.ev_vmt,
                "gas_vmt": res.gas_vmt,
                "co2_savings_tons": res.co2_savings_tons,
                "capex_per_ton_usd": res.capex_per_ton_usd,
            }
        )

    df = pd.DataFrame(rows)

    out_dir = PROJECT_ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "erev_scenario_grid.csv"

    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
