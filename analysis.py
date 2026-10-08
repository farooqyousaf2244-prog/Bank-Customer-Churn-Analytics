"""KPI and segmentation analysis on the cleaned dataset."""
from __future__ import annotations

import pandas as pd

from . import config as cfg


def kpis(df: pd.DataFrame) -> pd.DataFrame:
    churned = df[df["Exited"] == 1]
    rows = [
        ("Customers", len(df)),
        ("Churned Customers", int(df["Exited"].sum())),
        ("Churn Rate", df["Exited"].mean()),
        ("Average Credit Score", df["CreditScore"].mean()),
        ("Average Balance", df["Balance"].mean()),
        ("Average Estimated Salary", df["EstimatedSalary"].mean()),
        ("Balance Held by Churned Customers", churned["Balance"].sum()),
        ("Share of Total Balance Churned", churned["Balance"].sum() / df["Balance"].sum()),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"]).astype({"Value": object})


def segment_summary(df: pd.DataFrame, by, sort_by_rate: bool = False) -> pd.DataFrame:
    """Churn rate per segment, with lift and share of all churners.

    Lift = segment churn rate / overall churn rate (>1 means above average).
    """
    overall = df["Exited"].mean()
    total_churned = df["Exited"].sum()
    out = (
        df.groupby(by, observed=False)
        .agg(Customers=(cfg.KEY, "count"), Churned=("Exited", "sum"), Churn_Rate=("Exited", "mean"))
        .reset_index()
    )
    out["Lift_vs_Overall"] = out["Churn_Rate"] / overall
    out["Share_of_Churners"] = out["Churned"] / total_churned
    if sort_by_rate:
        out = out.sort_values("Churn_Rate", ascending=False).reset_index(drop=True)
    return out


def add_bands(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["AgeGroup"] = pd.cut(df["Age"], bins=cfg.AGE_BINS, labels=cfg.AGE_LABELS)
    df["CreditBand"] = pd.cut(df["CreditScore"], bins=cfg.CREDIT_BINS, labels=cfg.CREDIT_LABELS)
    return df


def high_value_churned(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    cols = [cfg.KEY, "Geography", "Age", "Balance", "NumOfProducts", "IsActiveMember"]
    return (
        df[df["Exited"] == 1].sort_values(["Balance", cfg.KEY], ascending=[False, True])[cols].head(top_n)
    )


def run_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    d = add_bands(df)
    return {
        "kpi_summary": kpis(d),
        "churn_by_geography": segment_summary(d, "Geography", sort_by_rate=True),
        "churn_by_gender": segment_summary(d, "Gender", sort_by_rate=True),
        "churn_by_activity": segment_summary(d, "IsActiveMember", sort_by_rate=True),
        "churn_by_products": segment_summary(d, "NumOfProducts"),
        "churn_by_age_group": segment_summary(d, "AgeGroup"),
        "churn_by_credit_band": segment_summary(d, "CreditBand"),
        "churn_by_geography_activity": segment_summary(d, ["Geography", "IsActiveMember"]),
        "high_value_churned": high_value_churned(d),
    }
