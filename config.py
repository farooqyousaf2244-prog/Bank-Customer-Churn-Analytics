"""Central configuration: paths, schema contract and business rules.

Every magic number or mapping used by the pipeline lives here so that
changes are made in one place and are easy to review.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("CHURN_PROJECT_ROOT", Path(__file__).resolve().parents[2]))


@dataclass(frozen=True)
class Paths:
    raw_workbook: Path = ROOT / "data" / "raw" / "Bank_Churn_Messy.xlsx"
    cleaned_csv: Path = ROOT / "data" / "cleaned" / "bank_churn_cleaned.csv"
    outputs: Path = ROOT / "outputs"
    figures: Path = ROOT / "outputs" / "figures"


PATHS = Paths()

# --- Raw workbook layout -----------------------------------------------------
CUSTOMER_SHEET = "Customer_Info"
ACCOUNT_SHEET = "Account_Info"
KEY_RAW = "CustomerId"
KEY = "CustomerID"

# --- Cleaning rules ----------------------------------------------------------
GEOGRAPHY_ALIASES = {
    "france": "France",
    "fra": "France",
    "french": "France",
    "germany": "Germany",
    "spain": "Spain",
}
YES_NO = {"yes": 1, "no": 0, "y": 1, "n": 0, "1": 1, "0": 0, "true": 1, "false": 0}
# Placeholder values found in the source system that mean "not captured".
SALARY_SENTINELS = (-999999.0,)
UNKNOWN_SURNAME = "Unknown"

# --- Output schema contract --------------------------------------------------
FINAL_COLUMNS = [
    "CustomerID", "Surname", "CreditScore", "Geography", "Gender", "Age", "Tenure",
    "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary", "Exited",
]

# --- Validation limits -------------------------------------------------------
ALLOWED_GEOGRAPHY = {"France", "Germany", "Spain"}
ALLOWED_GENDER = {"Male", "Female"}
CREDIT_SCORE_RANGE = (300, 850)
AGE_RANGE = (18, 100)
TENURE_RANGE = (0, 60)
PRODUCTS_RANGE = (1, 10)

# --- Segmentation (keep identical in sql/02_analysis.sql) ---------------------
AGE_BINS = [17, 25, 35, 45, 55, 65, 100]
AGE_LABELS = ["18-25", "26-35", "36-45", "46-55", "56-65", "66+"]
CREDIT_BINS = [0, 579, 669, 739, 799, 1000]
CREDIT_LABELS = ["Poor", "Fair", "Good", "Very Good", "Excellent"]
HIGH_VALUE_BALANCE = 100_000  # EUR balance threshold for "high-value" customers
