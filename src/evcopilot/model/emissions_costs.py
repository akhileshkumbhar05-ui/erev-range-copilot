from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ScenarioParams:
    # ... (same as before)
    name: str
    grid_co2_kg_per_kwh: float
    gas_co2_kg_per_litre: float
    ev_kwh_per_mile: float
    gas_litre_per_mile: float
    battery_kwh_per_mile_range: float
    battery_cost_usd_per_kwh: float
    electricity_price_usd_per_kwh: float
    gas_price_usd_per_litre: float


@dataclass
class EmissionsCostResult:
    # ... keep as before
    co2_ev_tons: float
    co2_gas_tons: float
    co2_baseline_tons: float
    co2_savings_tons: float
    battery_capex_usd: float
    capex_per_ton_usd: float
    ev_energy_cost_usd: float
    gas_fuel_cost_usd: float
    baseline_fuel_cost_usd: float
    net_operating_savings_usd: float


# NEW: lazy-loaded scenarios from YAML
_SCENARIOS_CACHE: Dict[str, ScenarioParams] | None = None


def _load_scenarios_if_needed() -> Dict[str, ScenarioParams]:
    global _SCENARIOS_CACHE
    if _SCENARIOS_CACHE is None:
        # Local import to avoid circular dependency
        from evcopilot.data.scenario_config import load_scenario_params_from_yaml

        _SCENARIOS_CACHE = load_scenario_params_from_yaml()
    return _SCENARIOS_CACHE


def get_scenario_params(name: str) -> ScenarioParams:
    scenarios = _load_scenarios_if_needed()
    if name not in scenarios:
        raise KeyError(f"Unknown scenario '{name}'. Valid: {list(scenarios)}")
    return scenarios[name]


def compute_emissions_and_costs(
    *,
    range_miles: float,
    ev_vmt: float,
    gas_vmt: float,
    params: ScenarioParams,
) -> EmissionsCostResult:
    """Compute CO2 and cost metrics for one EREV configuration.

    Arguments
    ---------
    range_miles:
        Rated electric range of the EREV (miles).
    ev_vmt:
        Annual miles run on electric power.
    gas_vmt:
        Annual miles run on gasoline.
    params:
        Scenario parameters.

    Returns
    -------
    EmissionsCostResult with CO2 and cost breakdowns.
    """

    total_vmt = ev_vmt + gas_vmt

    # Battery CAPEX from range
    battery_kwh = params.battery_kwh_per_mile_range * range_miles
    battery_capex_usd = battery_kwh * params.battery_cost_usd_per_kwh

    # Energy / fuel use
    ev_kwh = ev_vmt * params.ev_kwh_per_mile
    gas_litres = gas_vmt * params.gas_litre_per_mile

    # Baseline: all miles on gasoline (no electrification)
    baseline_litres = total_vmt * params.gas_litre_per_mile

    # CO2 emissions
    co2_ev_kg = ev_kwh * params.grid_co2_kg_per_kwh
    co2_gas_kg = gas_litres * params.gas_co2_kg_per_litre
    co2_baseline_kg = baseline_litres * params.gas_co2_kg_per_litre

    co2_ev_tons = co2_ev_kg / 1000.0
    co2_gas_tons = co2_gas_kg / 1000.0
    co2_baseline_tons = co2_baseline_kg / 1000.0
    co2_savings_tons = co2_baseline_tons - (co2_ev_tons + co2_gas_tons)

    # Operating costs
    ev_energy_cost_usd = ev_kwh * params.electricity_price_usd_per_kwh
    gas_fuel_cost_usd = gas_litres * params.gas_price_usd_per_litre
    baseline_fuel_cost_usd = baseline_litres * params.gas_price_usd_per_litre
    net_operating_savings_usd = baseline_fuel_cost_usd - (
        ev_energy_cost_usd + gas_fuel_cost_usd
    )

    # CAPEX per ton CO2 saved
    if co2_savings_tons > 0:
        capex_per_ton_usd = battery_capex_usd / co2_savings_tons
    else:
        capex_per_ton_usd = float("inf")

    return EmissionsCostResult(
        co2_ev_tons=co2_ev_tons,
        co2_gas_tons=co2_gas_tons,
        co2_baseline_tons=co2_baseline_tons,
        co2_savings_tons=co2_savings_tons,
        battery_capex_usd=battery_capex_usd,
        capex_per_ton_usd=capex_per_ton_usd,
        ev_energy_cost_usd=ev_energy_cost_usd,
        gas_fuel_cost_usd=gas_fuel_cost_usd,
        baseline_fuel_cost_usd=baseline_fuel_cost_usd,
        net_operating_savings_usd=net_operating_savings_usd,
    )
