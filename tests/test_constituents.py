import pandas as pd

from sp500_drawdowns.constituents import membership_at, membership_confidence


def _make():
    current = pd.DataFrame({"ticker": ["AAA", "BBB", "CCC"], "security": ["A", "B", "C"]})
    changes = pd.DataFrame(
        {
            "effective_date": pd.to_datetime(["2010-01-01", "2015-06-01", "2020-03-15"]),
            "added_ticker": ["AAA", "CCC", "BBB"],
            "removed_ticker": ["XXX", "YYY", "ZZZ"],
        }
    )
    return current, changes


def test_membership_today_is_current():
    current, changes = _make()
    members = membership_at(pd.Timestamp("2030-01-01"), current, changes)
    assert members == {"AAA", "BBB", "CCC"}


def test_membership_undoes_recent_change():
    current, changes = _make()
    # As of 2020-03-14: BBB hadn't been added yet, ZZZ hadn't been removed
    members = membership_at(pd.Timestamp("2020-03-14"), current, changes)
    assert "BBB" not in members
    assert "ZZZ" in members
    assert "AAA" in members
    assert "CCC" in members


def test_membership_chains_backward():
    current, changes = _make()
    # Before earliest change: undo all 3
    members = membership_at(pd.Timestamp("2009-01-01"), current, changes)
    assert members == {"XXX", "YYY", "ZZZ"}


def test_confidence_levels():
    current, changes = _make()
    assert membership_confidence(pd.Timestamp("2020-01-01"), changes) == "high"
    # pre-2000 but within range of changes
    pre = pd.DataFrame(
        {
            "effective_date": pd.to_datetime(["1990-01-01", "2010-01-01"]),
            "added_ticker": ["X", "Y"],
            "removed_ticker": ["P", "Q"],
        }
    )
    assert membership_confidence(pd.Timestamp("1995-01-01"), pre) == "medium"
    assert membership_confidence(pd.Timestamp("1980-01-01"), pre) == "low"
