"""Data-quality gate. Errors stop the pipeline; warnings are reported."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config as cfg


@dataclass
class Check:
    name: str
    passed: bool
    severity: str  # "error" | "warning"
    detail: str = ""


class ValidationError(Exception):
    pass


def _between(s: pd.Series, lo, hi) -> bool:
    return bool(s.between(lo, hi).all())


def run_checks(df: pd.DataFrame) -> list[Check]:
    c: list[Check] = []
    add = lambda name, ok, sev="error", detail="": c.append(Check(name, bool(ok), sev, detail))

    add("schema matches contract", list(df.columns) == cfg.FINAL_COLUMNS)
    add("dataset is not empty", len(df) > 0)
    add("CustomerID is unique", df[cfg.KEY].is_unique)
    add("no missing values", df.isna().sum().sum() == 0)
    add("Geography in allowed set", df["Geography"].isin(cfg.ALLOWED_GEOGRAPHY).all(),
        detail=str(sorted(set(df["Geography"]) - cfg.ALLOWED_GEOGRAPHY)))
    add("Gender in allowed set", df["Gender"].isin(cfg.ALLOWED_GENDER).all())
    add("CreditScore in range", _between(df["CreditScore"], *cfg.CREDIT_SCORE_RANGE))
    add("Age in range", _between(df["Age"], *cfg.AGE_RANGE))
    add("Tenure in range", _between(df["Tenure"], *cfg.TENURE_RANGE))
    add("NumOfProducts in range", _between(df["NumOfProducts"], *cfg.PRODUCTS_RANGE))
    add("Balance is non-negative", (df["Balance"] >= 0).all())
    add("EstimatedSalary is positive", (df["EstimatedSalary"] > 0).all(),
        detail=f"{int((df['EstimatedSalary'] <= 0).sum())} rows <= 0")
    for col in ("HasCrCard", "IsActiveMember", "Exited"):
        add(f"{col} is binary", df[col].isin([0, 1]).all())

    # Integrity warning: two flags that are always identical are usually a
    # sign of a mapping/extract problem upstream, not a real-world pattern.
    identical = (df["HasCrCard"] == df["IsActiveMember"]).all()
    add("HasCrCard differs from IsActiveMember", not identical, "warning",
        "columns are 100% identical - verify the source extract")
    return c


def validate(df: pd.DataFrame, strict: bool = True) -> list[Check]:
    checks = run_checks(df)
    failed = [x for x in checks if not x.passed and x.severity == "error"]
    if failed and strict:
        msg = "; ".join(f"{x.name} {x.detail}".strip() for x in failed)
        raise ValidationError(f"{len(failed)} data-quality check(s) failed: {msg}")
    return checks


def to_frame(checks: list[Check]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"Check": x.name, "Status": "PASS" if x.passed else "FAIL",
          "Severity": x.severity, "Detail": "" if x.passed else x.detail} for x in checks]
    )
