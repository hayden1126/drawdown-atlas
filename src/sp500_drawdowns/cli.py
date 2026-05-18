"""Pipeline CLI."""
from __future__ import annotations

import logging

import click

from . import constituents as cons
from . import drawdowns as dd
from . import factors as fac
from . import prices as px_mod
from . import ranking as rk
from . import regimes as reg
from . import report as rep


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    _setup_logging(verbose)


@cli.command()
@click.option("--force", is_flag=True, help="Re-download SPX data")
def drawdowns(force: bool) -> None:
    """Stage 1: detect SPX peak-to-trough drawdowns >=10%."""
    df = dd.run(force_download=force)
    click.echo(df.to_string(index=False))


@cli.command()
@click.option("--force", is_flag=True, help="Re-fetch Wikipedia tables")
def constituents(force: bool) -> None:
    """Stage 2: scrape Wikipedia constituent tables."""
    current, changes = cons.run(force_download=force)
    click.echo(f"current members: {len(current)}; changes: {len(changes)}")


@cli.command()
def prices() -> None:
    """Stage 3: download cached prices for all tickers needed across drawdowns."""
    import pandas as pd
    from .paths import DRAWDOWNS_CSV

    drawdowns_df = pd.read_csv(DRAWDOWNS_CSV, parse_dates=["peak_date"])
    current, changes = cons.fetch_wikipedia_tables()
    union: set[str] = set()
    for _, row in drawdowns_df.iterrows():
        union |= cons.membership_at(row["peak_date"], current, changes)
    click.echo(f"Universe size: {len(union)}")
    px_mod.download_missing(sorted(union))
    click.echo("Done.")


@cli.command()
def rank() -> None:
    """Stage 4: rank top 5 performers per drawdown."""
    df = rk.run()
    click.echo(f"Rows written: {len(df)}")


@cli.command()
def report() -> None:
    """Stage 5: render Markdown report."""
    text = rep.run()
    click.echo(text[:2000])


@cli.command()
def factors() -> None:
    """Stage 5: aggregate defensive-factor exposures across top-5 winners."""
    fac.run()
    click.echo("Defensive-factor report written.")


@cli.command()
def regimes() -> None:
    """Stage 6: classify drawdowns by regime (structural/cyclical/event-driven)."""
    reg.run()
    click.echo("Regime taxonomy report written.")


@cli.command()
def run() -> None:
    """Run the entire pipeline end-to-end."""
    dd.run()
    cons.run()
    rk.run()
    rep.run()
    click.echo("Pipeline complete.")


@cli.command("year")
@click.argument("year", type=int)
def year_cmd(year: int) -> None:
    """Within-calendar-year drawdown analysis: peak-to-trough legs >=10%."""
    cons.run()  # ensures Wikipedia tables cached
    drawdowns_df = dd.run_year(year)
    click.echo(f"Found {len(drawdowns_df)} within-{year} drawdown legs:")
    click.echo(drawdowns_df.to_string(index=False) if not drawdowns_df.empty else "(none)")
    if drawdowns_df.empty:
        rep.run_year(year)
        return
    rk.run_year(year)
    text = rep.run_year(year)
    click.echo("---")
    click.echo(text)


if __name__ == "__main__":
    cli()
