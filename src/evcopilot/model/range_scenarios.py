from __future__ import annotations

from dataclasses import dataclass

from evcopilot.model.emissions_costs import (
    EmissionsCostResult,
    ScenarioParams,
    compute_emissions_and_costs,
    get_scenario_params,
)
from evcopilot.model.vmt_bins import compute_ev_share_for_range


@dataclass
class RangeScenarioResult:
    range_miles: float
    charges_per_week: int
    scenario_name: str

    ev_share: float          # fraction of VMT that is electric (0–1)
    ev_vmt: float            # electric VMT (miles/year)
    gas_vmt: float           # gasoline VMT (miles/year)

    co2_savings_tons: float  # annual CO2 savings vs all-gas baseline
    capex_per_ton_usd: float # battery CAPEX per ton CO2 avoided


def _charging_frequency_multiplier(charges_per_week: int) -> float:
    """Heuristic adjustment for charging frequency.

    Interpretation:
    - Baseline EV share assumes 'reasonable' charging behaviour.
    - Fewer charges/week lose some potential EV miles (multiplier < 1).
    - Very frequent charging (7x) recovers a bit more EV miles.

    This is still a simplified representation and is a good place to plug in
    your weekly-profile model later.
    """
    return {
        2: 0.85,
        3: 0.90,
        5: 1.00,
        7: 1.05,
    }.get(charges_per_week, 1.0)


def compute_range_scenario(
    range_miles: float,
    charges_per_week: int,
    scenario_name: str = "Average",
    *,
    annual_vmt: float = 12_000.0,
) -> RangeScenarioResult:
    """High-level wrapper that drives the EREV scenario pipeline.

    Pipeline (current approximation):

    1. Use a trip-distance distribution to compute EV VMT share for the
       chosen electric range (assuming 'ideal' charging).
    2. Adjust EV share with a multiplier based on charges/week.
    3. Split annual VMT into EV vs gas miles.
    4. Apply emissions & cost model for the chosen scenario.
    """

    # 1. EV share from trip-bin model
    base_ev_share = compute_ev_share_for_range(range_miles)

    # 2. Charging frequency adjustment
    mult = _charging_frequency_multiplier(charges_per_week)
    ev_share = max(0.0, min(base_ev_share * mult, 1.0))

    # 3. EV vs gas miles
    ev_vmt = ev_share * annual_vmt
    gas_vmt = annual_vmt - ev_vmt

    # 4. Emissions and costs
    scenario_params: ScenarioParams = get_scenario_params(scenario_name)
    emissions_costs: EmissionsCostResult = compute_emissions_and_costs(
        range_miles=range_miles,
        ev_vmt=ev_vmt,
        gas_vmt=gas_vmt,
        params=scenario_params,
    )

    return RangeScenarioResult(
        range_miles=range_miles,
        charges_per_week=charges_per_week,
        scenario_name=scenario_name,
        ev_share=ev_share,
        ev_vmt=ev_vmt,
        gas_vmt=gas_vmt,
        co2_savings_tons=emissions_costs.co2_savings_tons,
        capex_per_ton_usd=emissions_costs.capex_per_ton_usd,
    )
