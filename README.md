 Bank Customer Churn Analytics

A reproducible analytics pipeline that cleans, validates and analyses retail-bank customer data to show who is leaving, where, and what it costs - and turns the result into retention recommendations.
Stack: Python (pandas), SQL (ANSI / PostgreSQL-compatible), Excel (source inspection).

 Business problem

Retention is cheaper than acquisition. The retention team needs to know which customer segments churn most, how much balance is at stake, and where to act first.

 Headline results

| Metric | Value |
|---|---|
| Customers analysed | 10,000 |
| Churn rate | 20.37% (2,037 customers) |
| Balance held by churned customers | EUR 185.6M (24.3% of total) |
| Highest-risk market | Germany - 32.4% churn, 40% of all churners |
| Highest-risk age bands | 46-55 and 56-65 - about 50% churn |
| Highest-risk combination | Inactive customers in Germany - 41.1% |
| Most stable group | Customers with exactly 2 products - 7.6% |

<p align="center">
  <img src="outputs/figures/churn_by_geography.png" width="48%">
  <img src="outputs/figures/churn_by_age_group.png" width="48%">
  <img src="outputs/figures/churn_by_products.png" width="48%">
  <img src="outputs/figures/churn_by_activity.png" width="48%">
</p>

Full findings, evidence and recommendations: [`docs/business_insights.md`](docs/business_insights.md).

> Open data issue: `HasCrCard` and `IsActiveMember` are identical in every row, which is almost certainly an upstream extract problem. The pipeline warns on each run. Details in [`docs/data_quality_report.md`](docs/data_quality_report.md).

 Quick start

```bash
pip install -r requirements.txt
make run          # raw workbook -> clean -> validate -> analyse -> charts
make analyze      # start from the cleaned CSV (no raw file needed)
make test         # 18 automated tests
```

Without `make`: `PYTHONPATH=src python -m churn_analytics run`.
Place `Bank_Churn_Messy.xlsx` (sheets `Customer_Info`, `Account_Info`) in `data/raw/` for the `run` / `clean` commands.

 How it works

```
Bank_Churn_Messy.xlsx
        |  cleaning.py      standardise, parse currency, handle missing/placeholder values, dedupe, join
        v
bank_churn_cleaned.csv
        |  validation.py    schema, uniqueness, ranges, categories  (fails the run on error)
        v
        |  analysis.py      KPIs + segment tables with churn rate, lift and share of churners
        v
outputs/*.csv  +  outputs/figures/*.png  +  sql/ (same analysis in SQL)
```

 Project structure

```text
bank-churn-analytics/
├── src/churn_analytics/
│   ├── config.py          paths, mappings, validation limits, segment definitions
│   ├── cleaning.py        raw -> clean (one small function per rule)
│   ├── validation.py      data-quality gate
│   ├── analysis.py        KPIs and segmentation
│   ├── reporting.py       charts
│   └── pipeline.py        CLI: run | clean | analyze
├── sql/
│   ├── 01_schema.sql      table with constraints and indexes
│   ├── 02_analysis.sql    11 business queries
│   └── 03_data_quality_checks.sql
├── tests/test_pipeline.py cleaning, validation, KPIs, SQL-vs-pandas parity
├── docs/
│   ├── business_insights.md
│   ├── data_quality_report.md
│   └── data_dictionary.md
├── data/{raw,cleaned}/
├── outputs/               CSV tables and figures
├── Makefile
└── requirements.txt
```

 Quality controls

- Validation gate: the pipeline stops if the key is not unique, categories or ranges are invalid, or nulls appear.
- Rules in one place: `config.py` holds mappings and thresholds; no magic numbers in the logic.
- Tests: unit tests on a deliberately messy fixture, plus reconciliation that segment tables sum to the dataset totals.
- SQL parity test:** the SQL queries are executed against the cleaned data and checked against the pandas results.
- Logged cleaning actions:** every imputation or removal is reported with a row count.

 Methodology notes

- Lift = segment churn rate / overall churn rate.
- Missing age and placeholder salaries are median-imputed (3 salary rows affected in the cleaned file).
- Segment cut-offs are identical in Python and SQL (`config.py` and `02_analysis.sql`).

 Limitations

Descriptive analysis only: it identifies where churn is high, not why, and it builds no predictive model. The data has no time dimension. Segments overlap, so rates are not additive.

 Possible next steps

Logistic-regression or gradient-boosting churn model with a hold-out evaluation; cost-benefit sizing of retention offers; scheduled refresh of the pipeline.
