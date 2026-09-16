# AstraPay Payment Profitability Capstone

Synthetic capstone submission for the AstraPay payment profitability diagnostic.

## Headline finding
Attempted volume increased from 29,591 in Jan-Mar 2026 to 45,409 in Apr-Jun 2026, but contribution profit per successful transaction fell from $0.105 to $-0.107. The decline is driven mainly by lower-margin merchant mix, more expensive routing/provider exposure, and a concentrated latency issue. Fraud controls and chargebacks contribute but are not sufficient as a single-cause explanation.

## Repository structure
- `data/`: generated source CSV files
- `01_problem_framing/`: SMART/MECE problem framing
- `02_data_contract/`: data contract workbook
- `03_dq_report/`: data quality scorecard workbook
- `04_sql/`: Snowflake SQL scripts and validation queries
- `05_profitability_model/`: model notes and transaction-level analytical output
- `06_powerbi/`: Power BI design and metric notes
- `07_executive_recommendation/`: executive recommendation deck
- `08_ai_usage_log/`: external AI validation log template
- `09_GitLab_MR/`: Git/GitLab instructions and MR description template
- `docs_for_student/`: non-submission reading guide
- `validation/`: computed summaries used by Excel/PPT/docs

## Verification
Run SQL files in order after loading data to Snowflake. Start with `04_sql/02_data_quality_checks.sql`, build the trusted model using `04_sql/03_trusted_profitability_model.sql`, then run `04_sql/04_validation_reconciliation.sql`.
