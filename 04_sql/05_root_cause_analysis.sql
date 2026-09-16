-- Root-cause analysis: locate deterioration and separate mix vs within-segment effect
USE DATABASE BANKING_ENTERPRISE_CAPSTONE;
USE SCHEMA CASE_STUDY;

-- Period-level executive KPI
WITH periodized AS (
  SELECT *, IFF(transaction_date < '2026-04-01','Baseline','Deterioration') AS period
  FROM FACT_TRANSACTION_PROFITABILITY
)
SELECT period, COUNT(*) AS attempts, SUM(successful_txn) AS successes,
       SUM(successful_txn)/COUNT(*) AS success_rate,
       SUM(contribution_profit_usd) AS contribution_profit_usd,
       SUM(contribution_profit_usd)/NULLIF(SUM(successful_txn),0) AS cp_per_success
FROM periodized
GROUP BY period;

-- Deterioration contribution by route/provider
WITH x AS (
  SELECT provider, route_id, IFF(transaction_date < '2026-04-01','Baseline','Deterioration') AS period,
         SUM(successful_txn) AS successes,
         SUM(contribution_profit_usd) AS profit
  FROM FACT_TRANSACTION_PROFITABILITY
  GROUP BY provider, route_id, period
), p AS (
  SELECT * FROM x
  PIVOT(SUM(successes) AS successes, SUM(profit) AS profit FOR period IN ('Baseline','Deterioration'))
)
SELECT provider, route_id,
       "'Baseline'_PROFIT"/NULLIF("'Baseline'_SUCCESSES",0) AS baseline_cp_per_success,
       "'Deterioration'_PROFIT"/NULLIF("'Deterioration'_SUCCESSES",0) AS deterioration_cp_per_success,
       (deterioration_cp_per_success - baseline_cp_per_success) * "'Deterioration'_SUCCESSES" AS deterioration_contribution_usd
FROM p
ORDER BY deterioration_contribution_usd ASC;

-- Mix vs within-segment effect by merchant segment
WITH seg AS (
  SELECT merchant_segment, IFF(transaction_date < '2026-04-01','Baseline','Deterioration') AS period,
         SUM(successful_txn) AS successes, SUM(contribution_profit_usd) AS profit
  FROM FACT_TRANSACTION_PROFITABILITY
  GROUP BY merchant_segment, period
), rates AS (
  SELECT merchant_segment, period, successes, profit, profit/NULLIF(successes,0) AS cp_rate,
         successes / SUM(successes) OVER (PARTITION BY period) AS success_share
  FROM seg
), wide AS (
  SELECT merchant_segment,
         MAX(IFF(period='Baseline', cp_rate, NULL)) AS base_rate,
         MAX(IFF(period='Deterioration', cp_rate, NULL)) AS det_rate,
         MAX(IFF(period='Baseline', success_share, NULL)) AS base_share,
         MAX(IFF(period='Deterioration', success_share, NULL)) AS det_share
  FROM rates
  GROUP BY merchant_segment
)
SELECT merchant_segment,
       (det_share - base_share) * base_rate AS mix_effect_per_txn,
       det_share * (det_rate - base_rate) AS within_effect_per_txn,
       ((det_share - base_share) * base_rate) + (det_share * (det_rate - base_rate)) AS total_effect_per_txn
FROM wide
ORDER BY total_effect_per_txn ASC;
