# scripts/build_knowledge_base.py

import sys
from pathlib import Path

# Ensure src/ is on the path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.rag.indexer import build_knowledge_base  # noqa: E402


if __name__ == "__main__":
    build_knowledge_base()
