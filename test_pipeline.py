"""Run with:  python -m unittest discover -s tests -v   (pytest also works)."""
import sqlite3
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from churn_analytics import config as cfg  # noqa: E402
from churn_analytics.analysis import run_analysis  # noqa: E402
from churn_analytics.cleaning import build_dataset, parse_currency, repair_cleaned  # noqa: E402
from churn_analytics.validation import ValidationError, validate  # noqa: E402

CLEANED = ROOT / "data" / "cleaned" / "bank_churn_cleaned.csv"


def messy_inputs():
    customer = pd.DataFrame({
        "CustomerId": [1, 2, 3, 4],
        "Surname": ["Smith", None, " Lee ", "Khan"],
        "CreditScore": [600, 700, 650, 720],
        "Geography": ["FRA", "French", "germany ", "Spain"],
        "Gender": [" male", "FEMALE", "Male", "female"],
        "Age": [30, np.nan, 45, 52],
        "Tenure": [1, 2, 3, 4],
        "EstimatedSalary": ["€50,000.50", "-999999", "€80,000", "€60,000"],
    })
    account = pd.DataFrame({
        "CustomerId": [1, 2, 2, 3, 4],  # row for customer 2 is an exact duplicate
        "Tenure": [1, 2, 2, 3, 4],
        "Balance": ["€0", "€1,000.00", "€1,000.00", "€2,500.25", "€10,000"],
        "NumOfProducts": [1, 2, 2, 1, 3],
        "HasCrCard": ["Yes", "No", "No", "Yes", "No"],
        "IsActiveMember": ["No", "Yes", "Yes", "Yes", "No"],
        "Exited": [0, 1, 1, 0, 1],
    })
    return customer, account


class CleaningTests(unittest.TestCase):
    def setUp(self):
        self.df = build_dataset(*messy_inputs())

    def test_duplicates_removed_and_key_unique(self):
        self.assertEqual(len(self.df), 4)
        self.assertTrue(self.df["CustomerID"].is_unique)

    def test_geography_standardised(self):
        self.assertEqual(self.df["Geography"].tolist(), ["France", "France", "Germany", "Spain"])

    def test_text_fields_normalised(self):
        self.assertEqual(self.df["Gender"].tolist(), ["Male", "Female", "Male", "Female"])
        self.assertEqual(self.df["Surname"].tolist(), ["Smith", "Unknown", "Lee", "Khan"])

    def test_sentinel_salary_is_imputed_not_kept(self):
        self.assertTrue((self.df["EstimatedSalary"] > 0).all())
        self.assertEqual(self.df.loc[1, "EstimatedSalary"], 60000.0)  # median of valid values

    def test_missing_age_imputed_and_integer(self):
        self.assertFalse(self.df["Age"].isna().any())
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["Age"]))

    def test_yes_no_mapped(self):
        self.assertEqual(self.df["HasCrCard"].tolist(), [1, 0, 1, 0])

    def test_output_passes_validation(self):
        validate(self.df)

    def test_currency_parser(self):
        self.assertEqual(parse_currency(pd.Series(["€1,234.50"])).iloc[0], 1234.5)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.df = build_dataset(*messy_inputs())

    def test_duplicate_key_fails(self):
        bad = pd.concat([self.df, self.df.head(1)], ignore_index=True)
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_unknown_geography_fails(self):
        bad = self.df.copy()
        bad.loc[0, "Geography"] = "Atlantis"
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_negative_salary_fails(self):
        bad = self.df.copy()
        bad.loc[0, "EstimatedSalary"] = -999999.0
        with self.assertRaises(ValidationError):
            validate(bad)


@unittest.skipUnless(CLEANED.exists(), "cleaned dataset not present")
class CleanedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = repair_cleaned(pd.read_csv(CLEANED))
        cls.res = run_analysis(cls.df)

    def test_validates(self):
        validate(self.df)

    def test_headline_kpis(self):
        k = self.res["kpi_summary"].set_index("Metric")["Value"]
        self.assertEqual(k["Customers"], 10000)
        self.assertEqual(k["Churned Customers"], 2037)
        self.assertAlmostEqual(k["Churn Rate"], 0.2037, places=4)

    def test_segments_reconcile_to_total(self):
        for name in ("churn_by_geography", "churn_by_products", "churn_by_age_group",
                     "churn_by_credit_band", "churn_by_gender", "churn_by_activity"):
            t = self.res[name]
            self.assertEqual(t["Customers"].sum(), 10000, name)
            self.assertEqual(t["Churned"].sum(), 2037, name)
            self.assertAlmostEqual(t["Share_of_Churners"].sum(), 1.0, places=9, msg=name)


@unittest.skipUnless(CLEANED.exists(), "cleaned dataset not present")
class SqlParityTests(unittest.TestCase):
    """The SQL deliverable must give the same answers as the pandas pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.df = repair_cleaned(pd.read_csv(CLEANED))
        cls.con = sqlite3.connect(":memory:")
        cls.con.executescript((ROOT / "sql" / "01_schema.sql").read_text())
        cls.df.to_sql("bank_churn", cls.con, if_exists="append", index=False)
        text = (ROOT / "sql" / "02_analysis.sql").read_text()
        cls.queries = [q.strip() for q in text.split(";") if "SELECT" in q]

    def q(self, i):
        return pd.read_sql_query(self.queries[i - 1], self.con)

    def test_all_queries_execute(self):
        self.assertEqual(len(self.queries), 11)
        for i in range(1, 12):
            self.q(i)

    def test_kpis(self):
        r = self.q(1).iloc[0]
        self.assertEqual(r["total_customers"], 10000)
        self.assertEqual(r["churned_customers"], 2037)
        self.assertAlmostEqual(r["churn_rate_pct"], 20.37, places=2)

    def test_geography(self):
        r = self.q(2).set_index("Geography")
        py = run_analysis(self.df)["churn_by_geography"].set_index("Geography")
        for g in r.index:
            self.assertAlmostEqual(r.loc[g, "churn_rate_pct"], 100 * py.loc[g, "Churn_Rate"], places=2)

    def test_age_and_credit_bands(self):
        res = run_analysis(self.df)
        for qi, key, col, lab in ((6, "churn_by_age_group", "age_group", "AgeGroup"),
                                  (7, "churn_by_credit_band", "credit_band", "CreditBand")):
            r = self.q(qi).set_index(col)
            py = res[key].set_index(lab)
            for k in r.index:
                self.assertEqual(r.loc[k, "customers"], py.loc[k, "Customers"], k)
                self.assertAlmostEqual(r.loc[k, "churn_rate_pct"], 100 * py.loc[k, "Churn_Rate"], places=2)


if __name__ == "__main__":
    unittest.main()
