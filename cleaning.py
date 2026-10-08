"""Raw workbook -> analysis-ready dataframe.

Each rule is a small, separately testable function. ``clean_data`` simply
composes them, so the order of operations is visible in one place.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config as cfg

log = logging.getLogger(__name__)


def standardize_geography(s: pd.Series) -> pd.Series:
    """Normalise country spellings (case/whitespace-insensitive).

    Values that are not in the alias map are kept as-is so that the
    validation step can reject them instead of silently hiding them.
    """
    key = s.astype(str).str.strip().str.lower()
    return key.map(cfg.GEOGRAPHY_ALIASES).fillna(s.astype(str).str.strip())


def parse_currency(s: pd.Series) -> pd.Series:
    """Convert strings such as '€1,234.50' to floats."""
    cleaned = (
        s.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def parse_yes_no(s: pd.Series) -> pd.Series:
    mapped = s.astype(str).str.strip().str.lower().map(cfg.YES_NO)
    if mapped.isna().any():
        bad = s[mapped.isna()].unique().tolist()
        raise ValueError(f"Unrecognised Yes/No values: {bad}")
    return mapped.astype(int)


def mask_sentinels(s: pd.Series, sentinels=cfg.SALARY_SENTINELS) -> pd.Series:
    """Turn 'not captured' placeholders (e.g. -999999) into NaN."""
    return s.mask(s.isin(sentinels) | (s <= 0))


def clean_customer(customer: pd.DataFrame) -> pd.DataFrame:
    customer = customer.copy()
    customer["Geography"] = standardize_geography(customer["Geography"])
    customer["Gender"] = customer["Gender"].astype(str).str.strip().str.title()
    customer["Surname"] = (
        customer["Surname"].fillna(cfg.UNKNOWN_SURNAME).astype(str).str.strip()
    )

    salary = mask_sentinels(parse_currency(customer["EstimatedSalary"]))
    n_salary = int(salary.isna().sum())
    if n_salary:
        log.info("EstimatedSalary: %d missing/sentinel values -> median imputation", n_salary)
    customer["EstimatedSalary"] = salary.fillna(salary.median())

    n_age = int(customer["Age"].isna().sum())
    if n_age:
        log.info("Age: %d missing values -> median imputation", n_age)
    customer["Age"] = customer["Age"].fillna(customer["Age"].median()).round().astype(int)
    return customer


def clean_account(account: pd.DataFrame) -> pd.DataFrame:
    before = len(account)
    account = account.drop_duplicates().copy()
    log.info("Account: removed %d exact duplicate rows", before - len(account))

    account["Balance"] = parse_currency(account["Balance"])
    for col in ("HasCrCard", "IsActiveMember"):
        account[col] = parse_yes_no(account[col])
    return account


def clean_data(raw_path=cfg.PATHS.raw_workbook) -> pd.DataFrame:
    log.info("Reading %s", raw_path)
    customer = pd.read_excel(raw_path, sheet_name=cfg.CUSTOMER_SHEET)
    account = pd.read_excel(raw_path, sheet_name=cfg.ACCOUNT_SHEET)
    return build_dataset(customer, account)


def build_dataset(customer: pd.DataFrame, account: pd.DataFrame) -> pd.DataFrame:
    """Clean both tables and join them on the customer key."""
    customer = clean_customer(customer)
    account = clean_account(account)

    df = customer.merge(
        account, on=cfg.KEY_RAW, how="inner", suffixes=("", "_account"),
        validate="one_to_one",
    )
    df = df.drop(columns=[c for c in df.columns if c.endswith("_account")])
    df = df.rename(columns={cfg.KEY_RAW: cfg.KEY})
    df = df[cfg.FINAL_COLUMNS].sort_values(cfg.KEY).reset_index(drop=True)
    log.info("Cleaned dataset: %d rows x %d columns", *df.shape)
    return df


def repair_cleaned(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the sentinel rule to an already-cleaned file (idempotent)."""
    df = df.copy()
    salary = mask_sentinels(df["EstimatedSalary"])
    n = int(salary.isna().sum())
    if n:
        log.info("Repaired %d sentinel salary values with the median", n)
    df["EstimatedSalary"] = salary.fillna(salary.median()).round(2)
    return df
