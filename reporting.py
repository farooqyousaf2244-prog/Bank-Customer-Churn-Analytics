"""Static charts for the README and stakeholder packs."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PRIMARY, ACCENT, GREY = "#1F4E79", "#C0392B", "#8C8C8C"


def _bar(df: pd.DataFrame, x: str, overall: float, title: str, path: Path, xlabel: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = df[x].astype(str)
    bars = ax.bar(labels, df["Churn_Rate"] * 100, color=PRIMARY)
    for b, r in zip(bars, df["Churn_Rate"]):
        if r > overall * 1.5:
            b.set_color(ACCENT)
        ax.annotate(f"{r:.1%}", (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=9)
    ax.axhline(overall * 100, color=GREY, ls="--", lw=1)
    ax.text(len(df) - 0.5, overall * 100 + 1, f"Overall {overall:.1%}", ha="right", color=GREY, fontsize=9)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Churn rate (%)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_figures(results: dict[str, pd.DataFrame], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    overall = float(results["kpi_summary"].set_index("Metric").loc["Churn Rate", "Value"])
    specs = [
        ("churn_by_geography", "Geography", "Churn rate by geography", "Geography"),
        ("churn_by_age_group", "AgeGroup", "Churn rate by age group", "Age group"),
        ("churn_by_products", "NumOfProducts", "Churn rate by number of products", "Products held"),
        ("churn_by_activity", "IsActiveMember", "Churn rate by activity status (0 = inactive)", "IsActiveMember"),
    ]
    paths = []
    for key, x, title, xlabel in specs:
        p = out_dir / f"{key}.png"
        _bar(results[key], x, overall, title, p, xlabel)
        paths.append(p)
    return paths
