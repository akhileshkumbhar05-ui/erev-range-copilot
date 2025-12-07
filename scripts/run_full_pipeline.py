from __future__ import annotations

import sys
from pathlib import Path

# -------------------------------------------------------------------
# Make sure src/ is on sys.path so "evcopilot" imports work
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # .../EREV-Project
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.model.erev_calculations import run_erev_analysis  # noqa: E402
from evcopilot.data.fhwa_api import (  # noqa: E402
    fetch_vm1_ldv_total_vmt_billion_miles,
)


def main() -> None:
    print("=== EREV Copilot – Full Pipeline (2023 only) ===")
    print(f"Project root: {PROJECT_ROOT}")

    out_dir = PROJECT_ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------
    # 1) Report the 2023 LDV VMT used in the analysis
    # ---------------------------------------------------------------
    vmt_ldv_2023_bil = fetch_vm1_ldv_total_vmt_billion_miles(2023)
    print(
        f"\n2023 LDV VMT used in EREV analysis: "
        f"{vmt_ldv_2023_bil:,.1f} billion miles"
    )

    # ---------------------------------------------------------------
    # 2) Run the EREV analytical calculations (paper-equivalent)
    # ---------------------------------------------------------------
    print("\n[1/1] Running EREV analytical calculations for 2023...")
    df_erev = run_erev_analysis(save_csv=True)

    erev_path = out_dir / "erev_calculations_results.csv"
    print(f"EREV calculations saved to: {erev_path}")

    print("\nEREV results (first 5 rows):")
    print(df_erev.round(3).head())

    print("\n=== Pipeline completed successfully ===")


if __name__ == "__main__":
    main()
