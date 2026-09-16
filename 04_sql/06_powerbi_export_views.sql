-- Optional export views for Power BI. Consume these governed objects, not raw tables.
USE DATABASE BANKING_ENTERPRISE_CAPSTONE;
USE SCHEMA CASE_STUDY;

CREATE OR REPLACE VIEW PBI_FACT_TRANSACTION_PROFITABILITY AS
SELECT * FROM FACT_TRANSACTION_PROFITABILITY;

CREATE OR REPLACE VIEW PBI_MONTHLY_KPI AS
SELECT DATE_TRUNC('month', transaction_date) AS month,
       COUNT(*) AS attempts,
       SUM(successful_txn) AS successes,
       SUM(successful_txn)/COUNT(*) AS success_rate,
       SUM(contribution_profit_usd) AS contribution_profit_usd,
       SUM(contribution_profit_usd)/NULLIF(SUM(successful_txn),0) AS cp_per_success_txn,
       SUM(processing_cost_usd) AS processing_cost_usd,
       SUM(merchant_fee_usd) AS merchant_fee_usd
FROM FACT_TRANSACTION_PROFITABILITY
GROUP BY month;

CREATE OR REPLACE VIEW PBI_ROUTE_DIAGNOSTIC AS
SELECT provider, route_id, country,
       COUNT(*) AS attempts, SUM(successful_txn) AS successes,
       SUM(successful_txn)/COUNT(*) AS success_rate,
       SUM(processing_cost_usd) AS processing_cost_usd,
       SUM(contribution_profit_usd) AS contribution_profit_usd,
       SUM(contribution_profit_usd)/NULLIF(SUM(successful_txn),0) AS cp_per_success_txn
FROM FACT_TRANSACTION_PROFITABILITY
GROUP BY provider, route_id, country;
