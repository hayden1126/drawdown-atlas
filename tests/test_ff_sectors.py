"""Tests for the Fama-French sector-portfolio stage."""
from __future__ import annotations

import pandas as pd

from sp500_drawdowns import ff_sectors as ffs


def _synthetic_ff(start: str = "2000-01-01", n: int = 60) -> pd.DataFrame:
    idx = pd.bdate_range(start, periods=n)
    data = {ind: [0.001] * n for ind in ffs.FF_INDUSTRIES}
    data["Enrgy"] = [0.01] * n
    df = pd.DataFrame(data, index=idx)
    df.index.name = "date"
    return df


def test_every_ff_industry_has_gics_mapping() -> None:
    for ind in ffs.FF_INDUSTRIES:
        assert ind in ffs.FF_TO_GICS
        assert ffs.FF_TO_GICS[ind]


def test_sector_returns_compound_correctly() -> None:
    df = _synthetic_ff(n=20)
    out = ffs.sector_returns_in_window(df, df.index[0], df.index[-1])
    assert 0.21 < out["Enrgy"] < 0.23
    assert 0.019 < out["NoDur"] < 0.022


def test_top_sectors_returns_ranked() -> None:
    df = _synthetic_ff(n=20)
    top = ffs.top_sectors(df, df.index[0], df.index[-1], n=3)
    assert len(top) == 3
    assert top.iloc[0]["ff_industry"] == "Enrgy"
    assert top.iloc[0]["gics_sector"] == "Energy"
    assert top.iloc[0]["rank"] == 1


def test_empty_window_returns_empty() -> None:
    df = _synthetic_ff(start="2000-01-01", n=20)
    assert ffs.sector_returns_in_window(df, pd.Timestamp("1995-01-01"), pd.Timestamp("1995-06-01")).empty
    assert ffs.top_sectors(df, pd.Timestamp("1995-01-01"), pd.Timestamp("1995-06-01")).empty


def test_ff_csv_parser_handles_header_and_section_boundary() -> None:
    sample = (
        "Header line ignored\n"
        "Another preamble line ignored\n"
        "\n"
        "  ,NoDur,Durbl,Manuf,Enrgy,Chems,BusEq,Telcm,Utils,Shops,Hlth,Money,Other\n"
        "19260701,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,1.00,1.10,1.20\n"
        "19260702,-0.10,-0.20,-0.30,-0.40,-0.50,-0.60,-0.70,-0.80,-0.90,-1.00,-1.10,-1.20\n"
        "\n"
        " Average Equal Weighted Returns -- Daily\n"
        "  ,NoDur,Durbl,Manuf,Enrgy,Chems,BusEq,Telcm,Utils,Shops,Hlth,Money,Other\n"
        "19260701,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10,0.11,0.12\n"
    )
    df = ffs._parse_ff_daily_csv(sample)
    assert len(df) == 2  # only the VW section
    assert abs(df.loc[pd.Timestamp("1926-07-01"), "NoDur"] - 0.001) < 1e-9
    assert abs(df.loc[pd.Timestamp("1926-07-02"), "Other"] + 0.012) < 1e-9
