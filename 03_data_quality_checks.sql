-- =============================================================================
-- Data-quality assertions. Every query should return 0 rows / 0 violations.
-- =============================================================================

-- Duplicate customers
SELECT CustomerID, COUNT(*) AS n FROM bank_churn GROUP BY CustomerID HAVING COUNT(*) > 1;

-- Non-positive salary or negative balance
SELECT COUNT(*) AS violations FROM bank_churn WHERE EstimatedSalary <= 0 OR Balance < 0;

-- Unexpected category values
SELECT DISTINCT Geography FROM bank_churn WHERE Geography NOT IN ('France', 'Germany', 'Spain');

-- Customers placed in 'Unknown' surname (informational; expected to be small)
SELECT COUNT(*) AS unknown_surname_rows FROM bank_churn WHERE Surname = 'Unknown';
