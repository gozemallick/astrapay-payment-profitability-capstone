# Payment profitability diagnostic capstone

## What changed
- Added synthetic AstraPay source datasets covering customers, merchants, transactions, events, fraud decisions, settlements, FX rates, route costs, chargebacks and merchant-risk snapshots.
- Added SMART/MECE executive problem framing.
- Added data contract and grain audit workbook.
- Added data-quality report workbook with defect counts and remediation decisions.
- Added reusable Snowflake SQL scripts for table creation, DQ checks, trusted profitability model, reconciliation, root-cause analysis and Power BI views.
- Added transaction-level profitability model documentation and Power BI design notes.
- Added executive recommendation deck and AI usage log template.

## Why
To answer why contribution profit per successful transaction is falling despite rising payment volume, while separating true business deterioration from data-quality artefacts.

## What was tested
- Transaction_id uniqueness and duplicate handling.
- Missing merchant_id counts.
- Fraud score validity.
- Late-arriving payment-event detection.
- Settlement coverage and multiple settlement rows per transaction.
- FX-rate type filtering.
- One-to-many join inflation check.
- Period-level KPI reconciliation.

## How to verify
1. Upload the CSV files under `data/` to the Snowflake stage.
2. Run `04_sql/01_create_tables_and_load.sql`.
3. Run `04_sql/02_data_quality_checks.sql`.
4. Run `04_sql/03_trusted_profitability_model.sql`.
5. Run `04_sql/04_validation_reconciliation.sql`.
6. Confirm the model row count equals distinct transaction_id count.
7. Open the Power BI design notes and build the dashboard using governed model outputs.

## Review evidence
Add actual peer-review comments/screenshots here after a reviewer checks the MR. Do not fabricate peer-review evidence.

## Secrets check
No credentials, access tokens, Snowflake passwords or personal secrets are committed.
