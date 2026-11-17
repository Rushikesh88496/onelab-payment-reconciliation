# ClearMatch — Payment Reconciliation

A Streamlit application for reconciling payment-platform transactions against bank settlement records. Built for the Onelab AI Fitness Assessment.

## Features
- Deterministic synthetic dataset with four planted exception types.
- CSV upload for platform and bank data.
- Transaction-ID + transaction-type matching.
- Late settlement detection across the reporting cutoff.
- Duplicate bank settlement detection.
- Orphan refund detection.
- Decimal-based currency handling and configurable tolerance.
- Exception table, summary metrics, chart, and CSV export.
- Automated tests using pytest.

## Run locally
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

## Run tests
```bash
pytest -q
```

## CSV schema
Platform transactions: `transaction_id, transaction_date, amount, type`

Bank settlements: `settlement_id, transaction_id, settlement_date, amount, type`

`type` is `payment` or `refund`. Dates should be parseable dates. Amounts are non-negative; type represents the direction/category.

## Deployment: Streamlit Community Cloud
1. Create a GitHub repository and push this folder.
2. Visit https://share.streamlit.io/ and sign in.
3. Choose the repository, branch, and `app.py`.
4. Deploy and test the public URL using the sample data.
5. Do not upload real customer or bank data to a public demo.

## Important assumptions
1. The platform transaction ID is the primary matching key; type is included to distinguish payments from refunds.
2. A settlement after the selected period end is classified as a timing difference if a matching transaction exists.
3. A duplicate is a repeated `(transaction_id, type)` in the bank file. The first occurrence is used for matching and subsequent occurrences are separately flagged.
4. Monetary values are represented to two decimal places using Decimal and ROUND_HALF_UP.
5. A one-cent tolerance is configurable; within-tolerance differences are shown separately rather than silently treated as exact matches.
6. The sample dataset is synthetic and uses October 2025 as its reporting period.
7. A refund is orphaned when the bank contains a refund reference for which no matching platform transaction of the same ID and type exists.

## Known limitations / production risks
- Real processors may use different identifiers, split/combined settlements, fees, reserves, chargebacks, FX conversion, and many-to-one mappings; ID-only matching would miss these relationships.
- The sample assumes a single currency and simple two-decimal amounts; production requires currency-aware precision, signed ledger entries, and explicit fee/tax treatment.
- The app does not yet provide immutable audit logs, role-based access, encrypted storage, approval workflows, or secure handling of sensitive financial data.

## Assessment submission note
Keep the genuine brainstorming and coding-agent execution transcripts from the tools you actually use. Do not present this README or the prepared prompts as a substitute for those raw logs.
