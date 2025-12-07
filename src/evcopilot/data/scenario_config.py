from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict

import yaml

from evcopilot.data.loaders import get_project_root
from evcopilot.model.emissions_costs import ScenarioParams


def _get_config_path() -> Path:
    root = get_project_root()
    return root / "config" / "erev_scenarios.yaml"


def load_scenario_params_from_yaml() -> Dict[str, ScenarioParams]:
    """Load all ScenarioParams objects from the YAML config."""
    path = _get_config_path()
    if not path.exists():
        raise FileNotFoundError(f"Scenario config not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if "scenarios" not in cfg:
        raise ValueError("Config file must have top-level 'scenarios' key")

    scenarios_cfg = cfg["scenarios"]
    out: Dict[str, ScenarioParams] = {}
    for name, values in scenarios_cfg.items():
        params = ScenarioParams(
            name=name,
            grid_co2_kg_per_kwh=float(values["grid_co2_kg_per_kwh"]),
            gas_co2_kg_per_litre=float(values["gas_co2_kg_per_litre"]),
            ev_kwh_per_mile=float(values["ev_kwh_per_mile"]),
            gas_litre_per_mile=float(values["gas_litre_per_mile"]),
            battery_kwh_per_mile_range=float(values["battery_kwh_per_mile_range"]),
            battery_cost_usd_per_kwh=float(values["battery_cost_usd_per_kwh"]),
            electricity_price_usd_per_kwh=float(values["electricity_price_usd_per_kwh"]),
            gas_price_usd_per_litre=float(values["gas_price_usd_per_litre"]),
        )
        out[name] = params

    return out


def dump_scenarios_to_dict() -> Dict[str, dict]:
    """Return scenarios as plain dicts (good for debugging / printing)."""
    scenarios = load_scenario_params_from_yaml()
    return {name: asdict(params) for name, params in scenarios.items()}
