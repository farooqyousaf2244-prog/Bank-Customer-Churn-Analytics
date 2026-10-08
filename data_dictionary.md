# Data Dictionary

Source: `data/cleaned/bank_churn_cleaned.csv` - one row per customer, 10,000 rows, 13 columns.

| Column | Type | Description | Rule / valid range |
|---|---|---|---|
| CustomerID | integer | Unique customer identifier (primary key) | Unique, not null |
| Surname | text | Customer surname | Missing values set to `Unknown` |
| CreditScore | integer | Credit score | 300-850 |
| Geography | text | Country of residence | `France`, `Germany`, `Spain` |
| Gender | text | Gender as recorded | `Male`, `Female` |
| Age | integer | Age in years | 18-100; missing values imputed with median |
| Tenure | integer | Years as a customer | >= 0 |
| Balance | decimal | Account balance (EUR) | >= 0 |
| NumOfProducts | integer | Number of bank products held | 1-4 observed |
| HasCrCard | 0/1 | Holds a credit card | Converted from Yes/No |
| IsActiveMember | 0/1 | Active in the recent period | Converted from Yes/No |
| EstimatedSalary | decimal | Estimated annual salary (EUR) | > 0; placeholder values imputed with median |
| Exited | 0/1 | **Target.** 1 = customer churned | Binary |

## Derived segments

| Segment | Definition |
|---|---|
| Age group | 18-25, 26-35, 36-45, 46-55, 56-65, 66+ |
| Credit band | Poor < 580, Fair 580-669, Good 670-739, Very Good 740-799, Excellent 800+ |
| Churn rate | Churned customers / customers in segment |
| Lift | Segment churn rate / overall churn rate (> 1 = above average risk) |
| Share of churners | Segment's churned customers / all churned customers |
