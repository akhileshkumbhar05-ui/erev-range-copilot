from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.model.vmt_bins import compute_ev_share_for_range


def main() -> None:
    ranges = np.arange(10, 201, 5)  # 10–200 miles
    shares = [compute_ev_share_for_range(r) for r in ranges]

    plt.figure(figsize=(7, 4))
    plt.plot(ranges, np.array(shares) * 100.0)
    plt.xlabel("EREV electric range (miles)")
    plt.ylabel("EV VMT share (%)")
    plt.title("EV VMT share vs EREV range (trip-bin model, placeholder params)")
    plt.grid(True)

    out_dir = PROJECT_ROOT / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ev_share_vs_range.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    main()
