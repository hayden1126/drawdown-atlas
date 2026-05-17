import pandas as pd

from sp500_drawdowns.drawdowns import find_drawdowns


def _series(values, start="2020-01-01"):
    idx = pd.bdate_range(start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def test_no_drawdown_for_monotonic_increase():
    s = _series([100, 101, 102, 103, 104, 105])
    assert find_drawdowns(s) == []


def test_shallow_dip_below_threshold_ignored():
    # 5% dip, below the 10% threshold
    s = _series([100, 95, 100, 105])
    assert find_drawdowns(s) == []


def test_single_drawdown_with_recovery():
    # peak at idx 0 (100), trough at idx 2 (80 = -20%), recovery at idx 4
    s = _series([100, 90, 80, 90, 100, 110])
    eps = find_drawdowns(s)
    assert len(eps) == 1
    e = eps[0]
    assert e.peak_close == 100
    assert e.trough_close == 80
    assert abs(e.max_dd - (-0.20)) < 1e-9
    assert e.peak_date == s.index[0]
    assert e.trough_date == s.index[2]
    assert e.recovery_date == s.index[4]


def test_two_separate_drawdowns():
    s = _series([100, 80, 110, 99, 88, 130])  # -20%, then -20% from 110
    eps = find_drawdowns(s)
    assert len(eps) == 2
    assert eps[0].peak_close == 100 and eps[0].trough_close == 80
    assert eps[1].peak_close == 110 and eps[1].trough_close == 88


def test_unrecovered_drawdown_at_series_end():
    s = _series([100, 95, 80, 70])  # -30% and never recovers
    eps = find_drawdowns(s)
    assert len(eps) == 1
    assert eps[0].recovery_date is None
    assert abs(eps[0].max_dd - (-0.30)) < 1e-9
