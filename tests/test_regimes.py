"""Tests for the regime-taxonomy stage."""
from __future__ import annotations

import numpy as np

from sp500_drawdowns import regimes as reg


def test_every_label_uses_a_known_regime() -> None:
    valid = {"structural", "cyclical", "event-driven"}
    for peak, (regime, rationale) in reg.REGIME_LABELS.items():
        assert regime in valid, f"Bad regime '{regime}' for {peak}"
        assert rationale and len(rationale) > 5, f"Rationale missing for {peak}"


def test_labels_match_known_drawdown_peaks() -> None:
    assert reg.REGIME_LABELS["1929-09-16"][0] == "structural"
    assert reg.REGIME_LABELS["1987-08-25"][0] == "event-driven"
    assert reg.REGIME_LABELS["2007-10-09"][0] == "structural"
    assert reg.REGIME_LABELS["2020-02-19"][0] == "event-driven"


def test_load_labels_returns_sorted_dataframe() -> None:
    df = reg.load_labels()
    assert list(df.columns) == ["peak_date", "regime", "rationale"]
    assert df["peak_date"].is_monotonic_increasing
    assert len(df) == len(reg.REGIME_LABELS)


def test_bootstrap_median_ci_bounds_contain_median() -> None:
    rng = np.random.default_rng(42)
    sample = rng.normal(loc=1.0, scale=0.2, size=80)
    med = float(np.median(sample))
    lo, hi = reg._bootstrap_median_ci(sample, n_boot=500, seed=1)
    assert lo <= med <= hi


def test_bootstrap_median_ci_empty_returns_nan() -> None:
    lo, hi = reg._bootstrap_median_ci(np.array([]))
    assert np.isnan(lo) and np.isnan(hi)
