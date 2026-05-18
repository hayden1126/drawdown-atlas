"""Tests for the defensive-factor aggregation stage."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sp500_drawdowns import factors as fac


def _make_market(n: int = 400, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    daily = rng.normal(loc=0.0004, scale=0.01, size=n)
    px = 100.0 * np.exp(np.cumsum(daily))
    idx = pd.bdate_range("2018-01-01", periods=n)
    return pd.Series(px, index=idx, name="SPX")


def _make_target(
    market: pd.Series, beta: float, sigma_idio: float, drift: float, seed: int = 1
) -> pd.Series:
    """Build a ticker whose log-returns are beta*market + idiosyncratic noise + drift."""
    rng = np.random.default_rng(seed)
    m_ret = np.log(market / market.shift(1)).dropna()
    idio = rng.normal(loc=drift, scale=sigma_idio, size=len(m_ret))
    t_ret = beta * m_ret.values + idio
    px = 50.0 * np.exp(np.cumsum(np.r_[0.0, t_ret]))
    return pd.Series(px, index=market.index, name="X")


def test_beta_recovery_within_tolerance() -> None:
    market = _make_market(n=400, seed=7)
    target = _make_target(market, beta=1.5, sigma_idio=0.005, drift=0.0, seed=11)
    peak = market.index[-1]
    f = fac.pre_drawdown_factors(target, market, peak)
    assert f is not None
    assert 1.2 <= f["pre_dd_beta"] <= 1.8


def test_vol_is_positive_and_reasonable() -> None:
    market = _make_market(n=400, seed=3)
    target = _make_target(market, beta=1.0, sigma_idio=0.01, drift=0.0, seed=5)
    peak = market.index[-1]
    f = fac.pre_drawdown_factors(target, market, peak)
    assert f is not None
    assert 0.1 < f["pre_dd_vol"] < 0.5


def test_returns_none_for_insufficient_data() -> None:
    market = _make_market(n=400, seed=2)
    short = _make_target(market, beta=1.0, sigma_idio=0.01, drift=0.0, seed=9).iloc[:20]
    peak = market.index[-1]
    assert fac.pre_drawdown_factors(short, market, peak) is None


def test_sector_fallback_used_when_yfinance_blank(monkeypatch, tmp_path) -> None:
    """If yfinance returns nothing, the hand-curated fallback dict should fill in."""
    monkeypatch.setattr(fac, "SECTOR_MAP_CACHE", tmp_path / "sector.parquet")

    class _FakeTicker:
        info: dict = {}

    class _FakeYF:
        @staticmethod
        def Ticker(_t):
            return _FakeTicker()

    import sys

    monkeypatch.setitem(sys.modules, "yfinance", _FakeYF())

    result = fac.fetch_sectors(["ED", "OKE"])
    assert result["ED"][0] == "Utilities"
    assert result["OKE"][0] == "Energy"
