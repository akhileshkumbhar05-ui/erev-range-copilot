from pathlib import Path
import sys

# Ensure src/ is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.app.dashboard import main


if __name__ == "__main__":
    main()
