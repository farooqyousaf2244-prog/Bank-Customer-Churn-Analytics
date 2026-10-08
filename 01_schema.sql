-- =============================================================================
-- Bank Customer Churn Analytics - schema
-- Dialect : ANSI-style SQL; verified on SQLite, compatible with PostgreSQL.
-- Load    : data/cleaned/bank_churn_cleaned.csv  ->  bank_churn
-- =============================================================================

DROP TABLE IF EXISTS bank_churn;

CREATE TABLE bank_churn (
    CustomerID      BIGINT        PRIMARY KEY,
    Surname         VARCHAR(100)  NOT NULL,
    CreditScore     INT           NOT NULL CHECK (CreditScore BETWEEN 300 AND 850),
    Geography       VARCHAR(50)   NOT NULL CHECK (Geography IN ('France', 'Germany', 'Spain')),
    Gender          VARCHAR(20)   NOT NULL CHECK (Gender IN ('Male', 'Female')),
    Age             INT           NOT NULL CHECK (Age BETWEEN 18 AND 100),
    Tenure          INT           NOT NULL CHECK (Tenure >= 0),
    Balance         DECIMAL(18,2) NOT NULL CHECK (Balance >= 0),
    NumOfProducts   INT           NOT NULL CHECK (NumOfProducts >= 1),
    HasCrCard       INT           NOT NULL CHECK (HasCrCard IN (0, 1)),
    IsActiveMember  INT           NOT NULL CHECK (IsActiveMember IN (0, 1)),
    EstimatedSalary DECIMAL(18,2) NOT NULL CHECK (EstimatedSalary > 0),
    Exited          INT           NOT NULL CHECK (Exited IN (0, 1))
);

CREATE INDEX idx_bank_churn_geography ON bank_churn (Geography);
CREATE INDEX idx_bank_churn_exited    ON bank_churn (Exited);
