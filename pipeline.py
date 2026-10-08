"""Command-line entry point.

    python -m churn_analytics run        # raw workbook -> clean -> validate -> analyse
    python -m churn_analytics clean      # raw workbook -> cleaned CSV only
    python -m churn_analytics analyze    # cleaned CSV  -> validate -> analyse
"""
from __future__ import annotations

import argparse
import logging
import sys

import pandas as pd

from . import config as cfg
from .analysis import run_analysis
from .cleaning import clean_data, repair_cleaned
from .reporting import make_figures
from .validation import ValidationError, to_frame, validate

log = logging.getLogger("churn_analytics")


def _write_outputs(df: pd.DataFrame, figures: bool = True) -> None:
    cfg.PATHS.outputs.mkdir(parents=True, exist_ok=True)
    checks = validate(df, strict=True)
    to_frame(checks).to_csv(cfg.PATHS.outputs / "data_quality_report.csv", index=False)
    for c in checks:
        if not c.passed:
            log.warning("WARNING: %s - %s", c.name, c.detail)

    results = run_analysis(df)
    for name, table in results.items():
        table.to_csv(cfg.PATHS.outputs / f"{name}.csv", index=False)
    if figures:
        make_figures(results, cfg.PATHS.figures)

    k = results["kpi_summary"].set_index("Metric")["Value"]
    log.info("Customers: %d | Churn rate: %.2f%%", k["Customers"], 100 * k["Churn Rate"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="churn_analytics", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["run", "clean", "analyze"])
    parser.add_argument("--no-figures", action="store_true", help="skip PNG chart generation")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    try:
        if args.command in ("run", "clean"):
            df = clean_data()
            validate(df, strict=True)
            cfg.PATHS.cleaned_csv.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(cfg.PATHS.cleaned_csv, index=False)
            log.info("Wrote %s", cfg.PATHS.cleaned_csv)
        else:
            df = repair_cleaned(pd.read_csv(cfg.PATHS.cleaned_csv))
        if args.command in ("run", "analyze"):
            _write_outputs(df, figures=not args.no_figures)
    except (ValidationError, FileNotFoundError, ValueError) as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
