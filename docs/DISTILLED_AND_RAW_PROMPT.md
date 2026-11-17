# Distilled build prompt

Build a production-minded but lightweight payment reconciliation prototype in Python, Pandas, and Streamlit. It must generate reproducible synthetic platform transactions and bank settlement rows for October 2025, deliberately including: (1) a platform transaction settled in November, (2) small per-row rounding differences that are visible in aggregate, (3) a duplicate bank settlement, and (4) an orphan bank refund with no platform original. Provide CSV uploads, schema validation, deterministic matching by transaction ID and type, Decimal currency arithmetic, configurable tolerance, late-settlement classification, duplicate detection, orphan refund detection, a row-level exception report, summary metrics, charts, and CSV export. Include pytest coverage for all four anomalies, exact match, missing settlement, and invalid duplicate platform IDs. Keep assumptions and production limitations explicit. Do not use an LLM for financial matching. Provide local run and deployment instructions. Inspect the existing project before changing anything if a project already exists; do not overwrite unrelated files.

# Raw prompt to use in Claude Code / Cursor

You are a senior Python engineer. Build the complete project described below in the current workspace.

BUSINESS PROBLEM:
A payments platform records transactions immediately. Its bank settles funds in batches, typically 1–2 days later. At month-end the platform transaction ledger and bank settlement ledger do not agree. Build a reconciliation tool that explains the differences.

REQUIREMENTS:
1. Use Python, Pandas, Streamlit, and pytest.
2. Generate deterministic synthetic data for October 2025. Include ordinary matching transactions and deliberately plant all these cases:
   - An October transaction whose settlement date is in November.
   - Small individual rounding variances whose sum is visible at the aggregate level.
   - A duplicate bank settlement row for one transaction.
   - A bank refund with no matching original platform transaction.
3. Accept uploaded CSVs with documented schemas.
4. Validate required columns, dates, IDs, transaction types, and non-negative amounts.
5. Match by transaction_id + type. Use Decimal for monetary comparisons, not binary float.
6. Distinguish exact matches, within-tolerance matches, amount mismatches, missing settlements, late settlements, duplicate bank rows, orphan refunds, and unmatched bank settlements.
7. Do not count duplicate rows twice in the unique bank settlement total.
8. Show platform total, bank total, gross difference, matched count, exception counts, and a detailed table.
9. Allow filtering and CSV export.
10. Write automated tests for all four planted cases, exact match, missing settlement, invalid input, and rounding.
11. Include README setup/deployment steps and clearly state assumptions and production limitations.
12. Do not claim the project is production-ready. Do not invent test results or deployment URLs.

WORKFLOW:
- First inspect the current workspace and report what exists.
- Then implement the smallest complete solution without unnecessary frameworks.
- Run the tests and fix failures.
- Run the app or perform a smoke test if possible.
- Summarize files changed, test results, how to run, and any remaining limitations.
