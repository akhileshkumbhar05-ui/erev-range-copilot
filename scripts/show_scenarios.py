from __future__ import annotations

from pathlib import Path
import sys
from pprint import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.data.scenario_config import dump_scenarios_to_dict


def main() -> None:
    scenarios = dump_scenarios_to_dict()
    print("Loaded scenarios from config/erev_scenarios.yaml:")
    pprint(scenarios)


if __name__ == "__main__":
    main()
