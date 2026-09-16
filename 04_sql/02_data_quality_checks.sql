-- Data quality checks: completeness, validity, uniqueness, timeliness, reconciliation
USE DATABASE BANKING_ENTERPRISE_CAPSTONE;
USE SCHEMA CASE_STUDY;

-- Duplicate transaction IDs: blocking
SELECT transaction_id, COUNT(*) AS row_count
FROM RAW_TRANSACTION
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- Missing merchant IDs: blocking for merchant/category/pricing analysis
SELECT COUNT(*) AS missing_merchant_id
FROM RAW_TRANSACTION
WHERE merchant_id IS NULL;

-- Zero or negative amount records: warning; retain with reversal/defect flag
SELECT COUNT(*) AS zero_or_negative_amount
FROM RAW_TRANSACTION
WHERE amount <= 0;

-- Fraud risk-score validity
SELECT COUNT(*) AS invalid_fraud_scores
FROM RAW_FRAUD_DECISION
WHERE risk_score < 0 OR risk_score > 1;

-- Late-arriving events > 3 days
SELECT COUNT(*) AS late_events_over_3_days
FROM RAW_PAYMENT_EVENT
WHERE DATEDIFF('day', event_time, ingestion_time) > 3;

-- Settlement coverage is not one-to-one with successful transactions
WITH successful AS (
  SELECT DISTINCT transaction_id FROM RAW_TRANSACTION WHERE status = 'SUCCESS'
), settled AS (
  SELECT DISTINCT transaction_id FROM RAW_SETTLEMENT
)
SELECT COUNT(*) AS successful_without_settlement
FROM successful s
LEFT JOIN settled x USING (transaction_id)
WHERE x.transaction_id IS NULL;

-- FX rate has multiple rate types, so all FX joins must filter rate_type explicitly
SELECT rate_date, currency, COUNT(DISTINCT rate_type) AS rate_type_count
FROM RAW_FX_RATE
GROUP BY rate_date, currency
HAVING COUNT(DISTINCT rate_type) > 1;
