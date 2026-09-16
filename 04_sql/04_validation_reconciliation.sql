-- Validation and reconciliation queries
USE DATABASE BANKING_ENTERPRISE_CAPSTONE;
USE SCHEMA CASE_STUDY;

-- Prove transaction-grain model has one row per transaction_id
SELECT COUNT(*) AS model_rows, COUNT(DISTINCT transaction_id) AS distinct_transactions
FROM FACT_TRANSACTION_PROFITABILITY;

-- Prove naive event join would inflate amount
WITH base AS (
  SELECT SUM(amount) AS base_amount FROM RAW_TRANSACTION
), naive AS (
  SELECT SUM(t.amount) AS naively_joined_amount
  FROM RAW_TRANSACTION t
  JOIN RAW_PAYMENT_EVENT e ON e.transaction_id = t.transaction_id
)
SELECT base_amount, naively_joined_amount, naively_joined_amount / NULLIF(base_amount,0) AS inflation_factor
FROM base, naive;

-- Settlement reconciliation: transaction-side successful GPV vs settlement-side amount
SELECT
  SUM(IFF(status='SUCCESS', amount_usd, 0)) AS transaction_success_gpv_usd,
  SUM(settlement_amount_usd) AS settlement_side_amount_usd
FROM (
  SELECT f.*, sa.settlement_amount_usd
  FROM FACT_TRANSACTION_PROFITABILITY f
  LEFT JOIN (
    SELECT s.transaction_id, SUM(s.settlement_amount * fx.rate_to_usd) AS settlement_amount_usd
    FROM RAW_SETTLEMENT s
    LEFT JOIN RAW_FX_RATE fx
      ON fx.currency = s.settlement_currency
     AND fx.rate_date = s.settlement_date
     AND fx.rate_type = 'SPOT'
    GROUP BY s.transaction_id
  ) sa USING (transaction_id)
);

-- KPI check by period
SELECT
  IFF(transaction_date < '2026-04-01','Baseline Jan-Mar','Deterioration Apr-Jun') AS period,
  COUNT(*) AS attempted,
  SUM(successful_txn) AS successful,
  SUM(successful_txn) / COUNT(*) AS success_rate,
  SUM(contribution_profit_usd) AS contribution_profit_usd,
  SUM(contribution_profit_usd) / NULLIF(SUM(successful_txn),0) AS contribution_profit_per_success_txn
FROM FACT_TRANSACTION_PROFITABILITY
GROUP BY period
ORDER BY period;
