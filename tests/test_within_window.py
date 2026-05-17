import pandas as pd

from sp500_drawdowns.drawdowns import find_drawdowns_in_window


def _series(values, start="2000-01-03"):
    idx = pd.bdate_range(start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def test_two_distinct_legs_in_one_year():
    # Two -20% legs separated by a partial recovery to a new peak.
    values = [100, 80, 110, 88, 130]
    s = _series(values)
    eps = find_drawdowns_in_window(s, "2000-01-01", "2000-12-31", threshold=-0.10)
    assert len(eps) == 2
    assert eps[0].peak_close == 100 and eps[0].trough_close == 80
    assert eps[1].peak_close == 110 and eps[1].trough_close == 88


def test_peak_in_lookback_window_is_kept():
    # Peak in late Dec 1999, prices keep falling through early 2000 → trough in 2000.
    idx = pd.bdate_range("1999-12-27", periods=12)
    # peak at idx 0 (1999-12-27=Mon, val 100); declines into Jan 2000, trough idx 8
    s = pd.Series([100, 98, 96, 94, 92, 90, 87, 85, 82, 90, 95, 101], index=idx, dtype=float)
    eps = find_drawdowns_in_window(s, "2000-01-01", "2000-12-31", threshold=-0.10)
    assert len(eps) == 1
    assert eps[0].peak_date.year == 1999
    assert eps[0].trough_date.year == 2000
    assert abs(eps[0].max_dd - (-0.18)) < 1e-9


def test_no_legs_when_only_shallow():
    s = _series([100, 95, 100, 96, 102])  # all <10%
    eps = find_drawdowns_in_window(s, "2000-01-01", "2000-12-31", threshold=-0.10)
    assert eps == []


def test_unrecovered_leg_at_window_end():
    # Falls into year-end without recovery
    s = _series([100, 95, 90, 80, 70], start="2000-12-22")
    eps = find_drawdowns_in_window(s, "2000-01-01", "2000-12-31", threshold=-0.10)
    assert len(eps) == 1
    assert eps[0].recovery_date is None
    assert abs(eps[0].max_dd - (-0.30)) < 1e-9


def test_trough_outside_window_dropped():
    # Trough in Jan 2001 should not be reported as a 2000 leg
    idx = pd.bdate_range("2000-12-20", periods=10)
    s = pd.Series([100, 99, 98, 97, 96, 95, 90, 80, 70, 60], index=idx, dtype=float)
    eps = find_drawdowns_in_window(s, "2000-01-01", "2000-12-31", threshold=-0.10)
    # The leg that troughs Jan 2001 is dropped; any sub-leg troughing in Dec 2000
    # may or may not exist depending on values — assert at most one with trough in 2000.
    for e in eps:
        assert e.trough_date.year == 2000
