from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np


@dataclass
class TripBin:
    """One trip distance bin."""

    lower: float          # inclusive, miles
    upper: float | None   # exclusive, miles; None = open-ended
    share_of_trips: float # fraction of all trips in this bin (0–1)

    @property
    def label(self) -> str:
        if self.upper is None:
            return f"{self.lower}+ mi"
        return f"{self.lower}–{self.upper} mi"

    @property
    def midpoint(self) -> float:
        """Representative distance in miles for this bin."""
        if self.upper is None:
            # For the open-ended bin we just pick a conservative value.
            return self.lower * 1.2
        return 0.5 * (self.lower + self.upper)


def default_trip_bins() -> List[TripBin]:
    """Return a placeholder US-like trip distance distribution.

    NOTE:
    - These shares are *not* calibrated to your paper yet.
    - They are intentionally simple and will be replaced later with BTS-based
      trip shares and/or the exact binning scheme from the manuscript.
    """

    # Example bins (miles) and rough trip shares (must sum ≈ 1.0)
    # 0–1, 1–3, 3–5, 5–10, 10–20, 20–30, 30–50, 50–100, 100+ miles
    bins: List[TripBin] = [
        TripBin(0.0, 1.0, 0.20),
        TripBin(1.0, 3.0, 0.25),
        TripBin(3.0, 5.0, 0.15),
        TripBin(5.0, 10.0, 0.15),
        TripBin(10.0, 20.0, 0.10),
        TripBin(20.0, 30.0, 0.06),
        TripBin(30.0, 50.0, 0.04),
        TripBin(50.0, 100.0, 0.03),
        TripBin(100.0, None, 0.02),
    ]

    total_share = sum(b.share_of_trips for b in bins)
    if not np.isclose(total_share, 1.0, atol=1e-6):
        # Normalise if the numbers are slightly off.
        for b in bins:
            b.share_of_trips /= total_share

    return bins


def compute_vmt_shares(bins: Sequence[TripBin]) -> Tuple[np.ndarray, np.ndarray]:
    """Compute each bin's share of total VMT given trip shares and midpoints.

    Returns
    -------
    vmt_shares : np.ndarray
        Shape (n_bins,), fraction of *total VMT* in each bin (sums to 1).
    distances  : np.ndarray
        Shape (n_bins,), representative distance of each bin (miles).
    """
    distances = np.array([b.midpoint for b in bins], dtype=float)
    trip_shares = np.array([b.share_of_trips for b in bins], dtype=float)

    # VMT contributed by each bin ∝ share_of_trips * distance
    raw_vmt = trip_shares * distances
    total_vmt = raw_vmt.sum()
    vmt_shares = raw_vmt / total_vmt
    return vmt_shares, distances


def compute_ev_share_for_range(
    range_miles: float,
    *,
    bins: Sequence[TripBin] | None = None,
) -> float:
    """Compute EV share of VMT for a given electric range.

    Assumptions:
    - Each trip in a bin has distance close to the bin midpoint.
    - For a trip of distance d:
        - EV covers `min(d, range_miles)` miles.
        - The rest, `max(0, d - range_miles)`, is gasoline.
    - We aggregate over the distance distribution to get EV VMT share.

    This is a clean, explainable model and a good starting point before
    plugging in the more detailed trip-bin methodology from your paper.
    """
    if bins is None:
        bins = default_trip_bins()

    vmt_shares, distances = compute_vmt_shares(bins)

    # For each bin, the fraction of that bin's VMT which is electric
    # = min(1, range / d) if d > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        frac_electric_per_bin = np.minimum(1.0, range_miles / np.maximum(distances, 1e-6))

    # Overall EV VMT share = sum_over_bins (bin VMT share × bin EV fraction)
    ev_share = float(np.dot(vmt_shares, frac_electric_per_bin))

    # Clamp numerically
    ev_share = max(0.0, min(ev_share, 1.0))
    return ev_share
