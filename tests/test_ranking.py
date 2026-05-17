import pandas as pd

from sp500_drawdowns.ranking import rank_drawdown


def _series(values, start="2020-01-01"):
    idx = pd.bdate_range(start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def test_top_n_ordering():
    peak = pd.Timestamp("2020-01-01")
    trough = pd.Timestamp("2020-01-06")  # 4 business days later
    universe = {"AA", "BB", "CC", "DD", "EE", "FF"}
    price_data = {
        "AA": _series([100, 90, 80, 70, 60]),    # -40% (worst)
        "BB": _series([100, 95, 90, 85, 80]),    # -20%
        "CC": _series([100, 102, 104, 106, 108]),# +8% (best)
        "DD": _series([100, 99, 98, 97, 96]),    # -4%
        "EE": _series([100, 101, 103, 105, 107]),# +7%
        "FF": _series([100, 100, 100, 100, 100]),# 0%
    }
    # trough is index 3 (2020-01-06 Mon), so each return is (s[3]-100)/100
    top = rank_drawdown(peak, trough, universe, price_data, top_n=5)
    assert len(top) == 5
    assert list(top["ticker"]) == ["CC", "EE", "FF", "DD", "BB"]
    assert top.iloc[0]["return_pct"] == 6.0
    assert top.iloc[-1]["return_pct"] == -15.0


def test_tickers_with_missing_data_skipped():
    peak = pd.Timestamp("2020-01-01")
    trough = pd.Timestamp("2020-01-06")
    universe = {"AA", "ZZ"}
    price_data = {
        "AA": _series([100, 90, 80, 70, 60]),
        # ZZ omitted entirely
    }
    top = rank_drawdown(peak, trough, universe, price_data)
    assert list(top["ticker"]) == ["AA"]
