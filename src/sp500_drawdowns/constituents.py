"""Stage 2: reconstruct point-in-time S&P 500 membership.

Scrapes Wikipedia's "List of S&P 500 companies" page (current members + the
"Selected changes" table) and walks the changes backward from today's set to
reconstruct membership at any historical date.
"""
from __future__ import annotations

import io
import logging
from datetime import date

import pandas as pd
import requests

from .paths import CHANGES_CACHE, CURRENT_MEMBERS_CACHE

log = logging.getLogger(__name__)

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
USER_AGENT = "sp500-drawdowns/0.1 (research; +https://example.invalid)"


def _normalize_ticker(t: str) -> str:
    """Wikipedia uses dots (e.g. BRK.B), yfinance uses dashes (BRK-B)."""
    if not isinstance(t, str):
        return ""
    return t.replace(".", "-").strip()


def fetch_wikipedia_tables(force: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (current_members_df, changes_df). Cached to parquet."""
    if CURRENT_MEMBERS_CACHE.exists() and CHANGES_CACHE.exists() and not force:
        return pd.read_parquet(CURRENT_MEMBERS_CACHE), pd.read_parquet(CHANGES_CACHE)

    log.info("Fetching %s ...", WIKI_URL)
    r = requests.get(WIKI_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    tables = pd.read_html(io.StringIO(r.text))

    current = tables[0].copy()
    current.columns = [str(c).strip() for c in current.columns]
    current = current.rename(columns={"Symbol": "ticker", "Security": "security"})
    current["ticker"] = current["ticker"].map(_normalize_ticker)
    current = current[["ticker", "security"]].dropna()
    current = current[current["ticker"] != ""].reset_index(drop=True)

    raw = tables[1].copy()
    # Multi-level header: flatten to "added_ticker", "added_security",
    # "removed_ticker", "removed_security", "effective_date", "reason"
    flat: dict[str, pd.Series] = {}
    for col in raw.columns:
        top, bottom = (col if isinstance(col, tuple) else (col, col))
        top_s = str(top).strip().lower().replace(" ", "_")
        bot_s = str(bottom).strip().lower().replace(" ", "_")
        if top_s == bot_s:
            key = top_s
        else:
            key = f"{top_s}_{bot_s}"
        flat[key] = raw[col]
    changes = pd.DataFrame(flat)

    # Some Wikipedia tables use a single repeated header row that becomes a data
    # row when flattened — drop rows where effective_date is literally the header.
    changes = changes[changes["effective_date"].astype(str).str.lower() != "effective date"]
    changes["effective_date"] = pd.to_datetime(
        changes["effective_date"], errors="coerce", format="mixed"
    )
    changes = changes.dropna(subset=["effective_date"])
    changes["added_ticker"] = changes.get("added_ticker", pd.Series(dtype=str)).map(_normalize_ticker)
    changes["removed_ticker"] = changes.get("removed_ticker", pd.Series(dtype=str)).map(_normalize_ticker)
    changes = changes.sort_values("effective_date").reset_index(drop=True)

    current.to_parquet(CURRENT_MEMBERS_CACHE)
    changes.to_parquet(CHANGES_CACHE)
    log.info("Cached %d current members and %d change rows", len(current), len(changes))
    return current, changes


def membership_at(
    as_of: date | pd.Timestamp,
    current_members: pd.DataFrame,
    changes: pd.DataFrame,
) -> set[str]:
    """Set of tickers that were S&P 500 members at end-of-day ``as_of``.

    Strategy: start with today's membership set, then walk every change with
    effective_date > as_of in **reverse chronological order**, undoing each:
    a ticker that was *added* on day D is removed (it wasn't a member before D);
    a ticker that was *removed* on day D is added back.
    """
    as_of_ts = pd.Timestamp(as_of)
    members: set[str] = set(current_members["ticker"].tolist())

    future_changes = changes[changes["effective_date"] > as_of_ts].sort_values(
        "effective_date", ascending=False
    )
    for _, row in future_changes.iterrows():
        added = row.get("added_ticker") or ""
        removed = row.get("removed_ticker") or ""
        if added:
            members.discard(added)
        if removed:
            members.add(removed)
    members.discard("")
    return members


def earliest_change_date(changes: pd.DataFrame) -> pd.Timestamp:
    return changes["effective_date"].min()


def membership_confidence(as_of: pd.Timestamp, changes: pd.DataFrame) -> str:
    """High / medium / low — coverage of the changes table degrades pre-2000."""
    as_of_ts = pd.Timestamp(as_of)
    if as_of_ts >= pd.Timestamp("2000-01-01"):
        return "high"
    if as_of_ts >= earliest_change_date(changes):
        return "medium"
    return "low"


def run(force_download: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    return fetch_wikipedia_tables(force=force_download)
