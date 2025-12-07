"""
EREV full analysis engine — replicates published paper equations.

Implements Sections 3.5–3.7 and 4.3–4.8 from:
'Contributions of Extended-Range Electric Vehicles (EREVs) to
Electrified Miles, Emissions and Transportation Cost Reduction.'

Author: Akhilesh Kumbhar et al.
"""
from __future__ import annotations
from pathlib import Path
import sys

# Ensure src/ is on sys.path when running this file directly
SRC_ROOT = Path(__file__).resolve().parents[2]  # .../src
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


import numpy as np
import pandas as pd
from pathlib import Path
from evcopilot.data.fhwa_api import fetch_vm1_ldv_total_vmt_miles

# ---------------------------------------------------------------------
# 1. Constants and default parameters
# ---------------------------------------------------------------------

VMT_TOTAL = fetch_vm1_ldv_total_vmt_miles(2023)          # Total U.S. 2023 VMT (miles)
VMT_PER_VEH = 11408            # Annual miles per vehicle
ETA_EV = 3.6                   # Vehicle efficiency (mi/kWh)
MPG = 26.4                     # Avg gasoline vehicle fuel economy
G_CO2_GRID = 348               # g/kWh U.S. grid
CBAT = 115                     # $/kWh battery cost
PE = 0.25                      # $/kWh retail electricity
PG = 3.0                       # $/gal gasoline
BATTERY_LIFE_YRS = 10          # assumed amortization period

GGAS = 8887 / MPG              # gCO2/mi for gasoline
GEV = (1 / ETA_EV) * G_CO2_GRID  # gCO2/mi for EV

# Trip-bin-based EV shares (range-miles -> EV share)
# Replace with computed from trip model later
EV_SHARE_BASE = {
    25: 0.55, 50: 0.733, 75: 0.79, 100: 0.84, 125: 0.86, 150: 0.868
}

# Scenario multipliers (grid intensity, battery cost, etc.)
SCENARIOS = {
    "Worst": {"grid_mult": 1.2, "cost_mult": 1.3},
    "Average": {"grid_mult": 1.0, "cost_mult": 1.0},
    "Best": {"grid_mult": 0.7, "cost_mult": 0.8},
}


# ---------------------------------------------------------------------
# 2. Helper functions
# ---------------------------------------------------------------------
def compute_fleet_size(vmt_total: float = VMT_TOTAL, vmt_per_vehicle: float = VMT_PER_VEH) -> float:
    return vmt_total / vmt_per_vehicle


def compute_battery_size(range_mi: float, eta: float = ETA_EV) -> float:
    return range_mi / eta  # kWh per vehicle


def compute_installed_capacity_twh(n_veh: float, range_mi: float) -> float:
    return (n_veh * compute_battery_size(range_mi)) / 1e9


def compute_ev_vmt_share(range_mi: float) -> float:
    if range_mi in EV_SHARE_BASE:
        return EV_SHARE_BASE[range_mi]
    # interpolate if needed
    keys, vals = zip(*sorted(EV_SHARE_BASE.items()))
    return float(np.interp(range_mi, keys, vals))


def compute_emissions(ev_vmt, gas_vmt, ggas=GGAS, gev=GEV) -> tuple[float, float, float]:
    """Return (EV_tons, Gas_tons, Savings_tons)."""
    ev_tons = (gev * ev_vmt) / 1e6
    gas_tons = (ggas * gas_vmt) / 1e6
    saved = gas_tons - ev_tons
    return ev_tons, gas_tons, saved


def compute_costs(range_mi, ev_vmt, co2_saved_tons, scenario="Average"):
    n_veh = compute_fleet_size()
    s = SCENARIOS[scenario]

    cbat_eff = CBAT * s["cost_mult"]
    grid_mult = s["grid_mult"]
    gev_eff = GEV * grid_mult

    s_kwh = compute_battery_size(range_mi)
    cfleet = n_veh * s_kwh * cbat_eff  # total battery CAPEX

    capex_per_evmi = cfleet / ev_vmt
    capex_per_ton = (cfleet / BATTERY_LIFE_YRS) / co2_saved_tons

    return {
        "Cfleet_USD": cfleet,
        "$/EV_mile": capex_per_evmi,
        "$/tCO2": capex_per_ton,
    }


# ---------------------------------------------------------------------
# 3. Main driver
# ---------------------------------------------------------------------
def run_erev_analysis(ranges=None, scenarios=None, save_csv=True):
    if ranges is None:
        ranges = [25, 50, 75, 100, 125, 150]
    if scenarios is None:
        scenarios = ["Worst", "Average", "Best"]

    n_veh = compute_fleet_size()
    results = []

    for sc in scenarios:
        for r in ranges:
            share = compute_ev_vmt_share(r)
            ev_vmt = VMT_TOTAL * share
            gas_vmt = VMT_TOTAL - ev_vmt

            ev_t, gas_t, saved_t = compute_emissions(ev_vmt, gas_vmt)
            installed_twh = compute_installed_capacity_twh(n_veh, r)

            cost_metrics = compute_costs(r, ev_vmt, saved_t, sc)

            results.append(
                {
                    "Scenario": sc,
                    "Range_mi": r,
                    "EV_share": share,
                    "EV_VMT": ev_vmt,
                    "Gas_VMT": gas_vmt,
                    "Installed_TWh": installed_twh,
                    "CO2_saved_tons": saved_t,
                    **cost_metrics,
                }
            )

    df = pd.DataFrame(results)
    df["CO2_saved_Mt"] = df["CO2_saved_tons"] / 1e6
    df["$ per EV-mile"] = df["$/EV_mile"]
    df["$ per ton CO2"] = df["$/tCO2"]

    if save_csv:
        out_dir = Path("data/processed")
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_dir / "erev_calculations_results.csv", index=False)

    return df


# ---------------------------------------------------------------------
# 4. Run standalone
# ---------------------------------------------------------------------
if __name__ == "__main__":
    df = run_erev_analysis()
    print(df.round(3))
