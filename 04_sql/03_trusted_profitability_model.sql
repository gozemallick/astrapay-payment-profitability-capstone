-- Trusted transaction-level profitability model
-- Grain: one row per unique transaction_id / payment attempt.
-- Rule: aggregate one-to-many sources before joining transaction-level amounts.

USE DATABASE BANKING_ENTERPRISE_CAPSTONE;
USE SCHEMA CASE_STUDY;

CREATE OR REPLACE TABLE FACT_TRANSACTION_PROFITABILITY AS
WITH transaction_dedup AS (
  SELECT *
  FROM RAW_TRANSACTION
  QUALIFY ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY created_at) = 1
),
pricing_plan_map AS (
  SELECT * FROM VALUES
    ('Standard', 0.019, 0.02),
    ('Growth', 0.015, 0.01),
    ('Enterprise', 0.022, 0.03),
    ('Promotional', 0.011, 0.00),
    ('High Risk', 0.026, 0.05)
  AS v(pricing_plan, variable_fee_pct, fixed_fee_usd)
),
fx_spot AS (
  SELECT rate_date, currency, rate_to_usd
  FROM RAW_FX_RATE
  WHERE rate_type = 'SPOT'
),
fx_accounting AS (
  SELECT rate_date, currency, rate_to_usd AS accounting_rate_to_usd
  FROM RAW_FX_RATE
  WHERE rate_type = 'ACCOUNTING'
),
event_agg AS (
  SELECT
    transaction_id,
    MAX(processing_ms) AS max_processing_ms,
    APPROX_PERCENTILE(processing_ms, 0.95) AS p95_processing_ms,
    MAX(IFF(DATEDIFF('day', event_time, ingestion_time) > 3, 1, 0)) AS late_event_flag
  FROM RAW_PAYMENT_EVENT
  GROUP BY transaction_id
),
settlement_agg AS (
  SELECT
    s.transaction_id,
    COUNT(*) AS settlement_count,
    SUM(ABS(s.fee_amount) * fx.rate_to_usd) AS settlement_fee_usd,
    SUM(s.settlement_amount * fx.rate_to_usd) AS settlement_amount_usd
  FROM RAW_SETTLEMENT s
  LEFT JOIN fx_spot fx
    ON fx.currency = s.settlement_currency
   AND fx.rate_date = s.settlement_date
  GROUP BY s.transaction_id
),
chargeback_agg AS (
  SELECT
    c.transaction_id,
    COUNT(*) AS chargeback_count,
    SUM(ABS(c.amount) * tx_fx.rate_to_usd) AS chargeback_cost_usd
  FROM RAW_CHARGEBACK c
  JOIN transaction_dedup t ON t.transaction_id = c.transaction_id
  LEFT JOIN fx_spot tx_fx
    ON tx_fx.currency = t.currency
   AND tx_fx.rate_date = CAST(t.created_at AS DATE)
  GROUP BY c.transaction_id
),
merchant_risk_dedup AS (
  SELECT merchant_id, snapshot_month, AVG(risk_score) AS snapshot_risk_score, MAX(risk_band) AS snapshot_risk_band
  FROM RAW_MERCHANT_RISK_SNAPSHOT
  GROUP BY merchant_id, snapshot_month
)
SELECT
  t.transaction_id,
  t.customer_id,
  t.merchant_id,
  t.created_at,
  CAST(t.created_at AS DATE) AS transaction_date,
  DATE_TRUNC('month', t.created_at) AS transaction_month,
  t.amount,
  t.currency,
  t.amount * fx.rate_to_usd AS amount_usd,
  t.channel,
  t.status,
  t.route_id,
  m.merchant_segment,
  m.category,
  m.country,
  m.pricing_plan,
  m.risk_tier,
  rc.provider,
  rc.region,
  IFF(t.status = 'SUCCESS', 1, 0) AS successful_txn,
  IFF(t.status = 'SUCCESS', ABS(t.amount * fx.rate_to_usd) * ppm.variable_fee_pct + ppm.fixed_fee_usd, 0) AS merchant_fee_usd,
  rc.fixed_fee + ABS(t.amount * fx.rate_to_usd) * rc.variable_fee_pct AS processing_cost_usd,
  COALESCE(sa.settlement_fee_usd, 0) AS settlement_fee_usd,
  COALESCE(ca.chargeback_cost_usd, 0) AS chargeback_cost_usd,
  IFF(t.status = 'DECLINED_FRAUD', ABS(t.amount * fx.rate_to_usd) * 0.0025, 0) AS fraud_control_cost_usd,
  IFF(t.status = 'SUCCESS', (t.amount * fx.rate_to_usd) - (t.amount * fa.accounting_rate_to_usd), 0) AS fx_impact_usd,
  COALESCE(ea.p95_processing_ms, ea.max_processing_ms) AS processing_ms_for_analysis,
  COALESCE(ea.late_event_flag,0) AS late_event_flag,
  COALESCE(sa.settlement_count,0) AS settlement_count,
  COALESCE(ca.chargeback_count,0) AS chargeback_count,
  mr.snapshot_risk_score,
  mr.snapshot_risk_band,
  /* Final contribution economics */
  (IFF(t.status = 'SUCCESS', ABS(t.amount * fx.rate_to_usd) * ppm.variable_fee_pct + ppm.fixed_fee_usd, 0)
   - (rc.fixed_fee + ABS(t.amount * fx.rate_to_usd) * rc.variable_fee_pct)
   - COALESCE(sa.settlement_fee_usd, 0)
   - COALESCE(ca.chargeback_cost_usd, 0)
   - IFF(t.status = 'DECLINED_FRAUD', ABS(t.amount * fx.rate_to_usd) * 0.0025, 0)
   + IFF(t.status = 'SUCCESS', (t.amount * fx.rate_to_usd) - (t.amount * fa.accounting_rate_to_usd), 0)
  ) AS contribution_profit_usd
FROM transaction_dedup t
LEFT JOIN RAW_MERCHANT m ON m.merchant_id = t.merchant_id
LEFT JOIN pricing_plan_map ppm ON ppm.pricing_plan = m.pricing_plan
LEFT JOIN fx_spot fx ON fx.currency = t.currency AND fx.rate_date = CAST(t.created_at AS DATE)
LEFT JOIN fx_accounting fa ON fa.currency = t.currency AND fa.rate_date = CAST(t.created_at AS DATE)
LEFT JOIN RAW_ROUTE_COST rc ON rc.route_id = t.route_id AND rc.cost_date = CAST(t.created_at AS DATE)
LEFT JOIN event_agg ea ON ea.transaction_id = t.transaction_id
LEFT JOIN settlement_agg sa ON sa.transaction_id = t.transaction_id
LEFT JOIN chargeback_agg ca ON ca.transaction_id = t.transaction_id
LEFT JOIN merchant_risk_dedup mr ON mr.merchant_id = t.merchant_id AND mr.snapshot_month = DATE_TRUNC('month', t.created_at);
