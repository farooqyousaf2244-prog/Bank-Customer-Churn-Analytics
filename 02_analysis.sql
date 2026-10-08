-- =============================================================================
-- Bank Customer Churn Analytics - analysis queries
-- Run after 01_schema.sql and loading the cleaned CSV.
-- Definitions: churn_rate_pct = 100 * churned / customers
--              lift           = segment churn rate / overall churn rate
-- Segment cut-offs match src/churn_analytics/config.py.
-- =============================================================================

-- 01. Executive KPIs ---------------------------------------------------------
SELECT
    COUNT(*)                                          AS total_customers,
    SUM(Exited)                                       AS churned_customers,
    ROUND(100.0 * SUM(Exited) / COUNT(*), 2)          AS churn_rate_pct,
    ROUND(AVG(CreditScore), 2)                        AS avg_credit_score,
    ROUND(AVG(Balance), 2)                            AS avg_balance,
    ROUND(AVG(EstimatedSalary), 2)                    AS avg_estimated_salary,
    ROUND(SUM(CASE WHEN Exited = 1 THEN Balance ELSE 0 END), 2) AS balance_at_churned_customers,
    ROUND(100.0 * SUM(CASE WHEN Exited = 1 THEN Balance ELSE 0 END) / SUM(Balance), 2) AS pct_balance_churned
FROM bank_churn;

-- 02. Churn by geography (with lift and share of all churners) ---------------
WITH overall AS (
    SELECT 1.0 * SUM(Exited) / COUNT(*) AS rate, SUM(Exited) AS churned FROM bank_churn
)
SELECT b.Geography,
       COUNT(*)                                              AS customers,
       SUM(b.Exited)                                         AS churned_customers,
       ROUND(100.0 * SUM(b.Exited) / COUNT(*), 2)            AS churn_rate_pct,
       ROUND((1.0 * SUM(b.Exited) / COUNT(*)) / o.rate, 2)   AS lift,
       ROUND(100.0 * SUM(b.Exited) / o.churned, 2)           AS pct_of_all_churners
FROM bank_churn b
CROSS JOIN overall o
GROUP BY b.Geography, o.rate, o.churned
ORDER BY churn_rate_pct DESC;

-- 03. Churn by gender --------------------------------------------------------
SELECT Gender,
       COUNT(*)                                   AS customers,
       SUM(Exited)                                AS churned_customers,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)   AS churn_rate_pct
FROM bank_churn
GROUP BY Gender
ORDER BY churn_rate_pct DESC;

-- 04. Churn by activity status -----------------------------------------------
SELECT IsActiveMember,
       COUNT(*)                                   AS customers,
       SUM(Exited)                                AS churned_customers,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)   AS churn_rate_pct
FROM bank_churn
GROUP BY IsActiveMember
ORDER BY churn_rate_pct DESC;

-- 05. Churn by number of products --------------------------------------------
SELECT NumOfProducts,
       COUNT(*)                                   AS customers,
       SUM(Exited)                                AS churned_customers,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)   AS churn_rate_pct
FROM bank_churn
GROUP BY NumOfProducts
ORDER BY NumOfProducts;

-- 06. Churn by age group -----------------------------------------------------
WITH banded AS (
    SELECT Exited,
           CASE
               WHEN Age <= 25 THEN '18-25'
               WHEN Age <= 35 THEN '26-35'
               WHEN Age <= 45 THEN '36-45'
               WHEN Age <= 55 THEN '46-55'
               WHEN Age <= 65 THEN '56-65'
               ELSE '66+'
           END AS age_group
    FROM bank_churn
)
SELECT age_group,
       COUNT(*)                                   AS customers,
       SUM(Exited)                                AS churned_customers,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)   AS churn_rate_pct
FROM banded
GROUP BY age_group
ORDER BY age_group;

-- 07. Churn by credit-score band ---------------------------------------------
WITH banded AS (
    SELECT Exited,
           CASE
               WHEN CreditScore < 580 THEN 'Poor'
               WHEN CreditScore < 670 THEN 'Fair'
               WHEN CreditScore < 740 THEN 'Good'
               WHEN CreditScore < 800 THEN 'Very Good'
               ELSE 'Excellent'
           END AS credit_band
    FROM bank_churn
)
SELECT credit_band,
       COUNT(*)                                   AS customers,
       SUM(Exited)                                AS churned_customers,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)   AS churn_rate_pct
FROM banded
GROUP BY credit_band
ORDER BY churn_rate_pct DESC;

-- 08. Geography x activity (where is retention risk concentrated?) -----------
SELECT Geography,
       IsActiveMember,
       COUNT(*)                                   AS customers,
       SUM(Exited)                                AS churned_customers,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)   AS churn_rate_pct
FROM bank_churn
GROUP BY Geography, IsActiveMember
ORDER BY Geography, IsActiveMember;

-- 09. Top 20 high-value churned customers (win-back candidates) --------------
SELECT CustomerID, Geography, Age, Balance, NumOfProducts, IsActiveMember
FROM bank_churn
WHERE Exited = 1
ORDER BY Balance DESC, CustomerID
LIMIT 20;

-- 10. Retained high-value customers at risk (inactive, balance >= 100k) ------
SELECT Geography,
       COUNT(*)                     AS customers,
       ROUND(SUM(Balance), 2)       AS balance_at_risk
FROM bank_churn
WHERE Exited = 0
  AND IsActiveMember = 0
  AND Balance >= 100000
GROUP BY Geography
ORDER BY balance_at_risk DESC;

-- 11. Rank geographies within each activity status (window function) ---------
SELECT IsActiveMember,
       Geography,
       ROUND(100.0 * SUM(Exited) / COUNT(*), 2)                          AS churn_rate_pct,
       RANK() OVER (PARTITION BY IsActiveMember
                    ORDER BY 1.0 * SUM(Exited) / COUNT(*) DESC)          AS risk_rank
FROM bank_churn
GROUP BY IsActiveMember, Geography
ORDER BY IsActiveMember, risk_rank;
