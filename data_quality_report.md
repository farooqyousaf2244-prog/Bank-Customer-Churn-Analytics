# Data Quality Report

## Cleaning rules applied (raw workbook -> cleaned CSV)

| # | Issue in raw data | Treatment | Why |
|---|---|---|---|
| 1 | Exact duplicate rows in `Account_Info` | Removed | Prevents double-counting customers |
| 2 | Inconsistent country labels (`FRA`, `French`, `France`) | Mapped to one standard value (case/whitespace-insensitive) | Correct segment counts |
| 3 | Currency stored as text (`EUR 1,234.50` style) | Parsed to numeric | Enables aggregation |
| 4 | Missing surname | Set to `Unknown` | Keeps the row; surname is not used in analysis |
| 5 | Missing age | Median imputation | Few rows affected; median is robust to outliers |
| 6 | Salary placeholder value `-999999` | Treated as missing, then median imputation | A sentinel is not a real salary and distorts averages |
| 7 | Yes/No flags | Converted to 1/0 | Numeric analysis |
| 8 | Two source tables | Joined on customer key with a one-to-one check | Guarantees one record per customer |

## Automated validation gate

`python -m churn_analytics run` fails (non-zero exit) if any **error** check fails:
schema contract, non-empty dataset, unique `CustomerID`, no nulls, allowed categories,
numeric ranges, non-negative balance, positive salary, binary flags.
The latest results are written to `outputs/data_quality_report.csv`.

## Findings from this review

| Severity | Finding | Impact | Action |
|---|---|---|---|
| Fixed | 3 rows still carried the `-999999` salary placeholder in the cleaned file (all 3 also had `Unknown` surname). | Average salary was understated (99,762 vs 100,092). | Treated as missing and median-imputed; rule added to the pipeline and covered by tests. |
| **Open - needs owner** | `HasCrCard` and `IsActiveMember` are **identical in all 10,000 rows** (both 51.5% = 1). | Two flags that always match are very unlikely in real data. Either one column was derived from the other during extraction, or the mapping is wrong. Any conclusion about credit-card ownership is unreliable, and the "inactive member" insight carries the same caveat. | Confirm against the source system. The pipeline raises a warning on every run until the columns differ. |
| Note | Median imputation reduces variance for the imputed fields. | Minimal at this volume (3 salary rows; age imputation per raw data). | Documented; revisit if missingness grows. |
