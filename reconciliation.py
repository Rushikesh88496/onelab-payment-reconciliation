from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Tuple
import pandas as pd

CENT = Decimal("0.01")

def money(value) -> Decimal:
    """Convert a value to currency-safe Decimal, rounded to cents."""
    try:
        return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Invalid monetary value: {value!r}")

def validate_transactions(df: pd.DataFrame) -> None:
    required = {"transaction_id", "transaction_date", "amount", "type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Transactions file missing columns: {sorted(missing)}")
    if df["transaction_id"].isna().any():
        raise ValueError("Transactions contain blank transaction_id values")
    if df["transaction_id"].duplicated().any():
        raise ValueError("Transactions contain duplicate transaction_id values")
    if not set(df["type"].astype(str).str.lower()).issubset({"payment", "refund"}):
        raise ValueError("Transaction type must be payment or refund")
    pd.to_datetime(df["transaction_date"], errors="raise")
    for value in df["amount"]:
        if money(value) < 0:
            raise ValueError("Amounts must be non-negative; use type to indicate refunds")

def validate_settlements(df: pd.DataFrame) -> None:
    required = {"settlement_id", "transaction_id", "settlement_date", "amount", "type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Settlements file missing columns: {sorted(missing)}")
    if df["settlement_id"].isna().any():
        raise ValueError("Settlements contain blank settlement_id values")
    pd.to_datetime(df["settlement_date"], errors="raise")
    for value in df["amount"]:
        if money(value) < 0:
            raise ValueError("Amounts must be non-negative; use type to indicate refunds")

def reconcile(transactions: pd.DataFrame, settlements: pd.DataFrame,
              period_start="2025-10-01", period_end="2025-10-31",
              tolerance="0.01") -> Tuple[pd.DataFrame, Dict]:
    """
    Reconcile platform transactions in a reporting period against bank records.

    Matching policy:
    - Transaction ID + transaction type is the primary key.
    - Duplicate bank rows for the same transaction/type are flagged; only the
      first is counted for the primary match to avoid inflating totals.
    - A matching settlement after period_end is a timing difference.
    - Refunds without an original platform transaction are orphan refunds.
    - Amount differences <= tolerance are considered rounding/tolerance matches.
    - Amounts are converted to Decimal cents before comparison.
    """
    validate_transactions(transactions)
    validate_settlements(settlements)

    tx = transactions.copy()
    st = settlements.copy()
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"]).dt.date
    st["settlement_date"] = pd.to_datetime(st["settlement_date"]).dt.date
    tx["type"] = tx["type"].str.lower()
    st["type"] = st["type"].str.lower()
    tx["amount_dec"] = tx["amount"].map(money)
    st["amount_dec"] = st["amount"].map(money)

    start, end = pd.Timestamp(period_start).date(), pd.Timestamp(period_end).date()
    tol = money(tolerance)
    tx_period = tx[(tx["transaction_date"] >= start) & (tx["transaction_date"] <= end)].copy()

    # Duplicate key means repeated settlement for the same transaction/type.
    st["duplicate_key"] = st.duplicated(["transaction_id", "type"], keep="first")
    st_period = st[(st["settlement_date"] >= start) & (st["settlement_date"] <= end)].copy()
    duplicate_rows = st[st["duplicate_key"]].copy()
    st_unique = st[~st["duplicate_key"]].copy()

    tx_lookup = {(r.transaction_id, r.type): r for r in tx.itertuples()}
    st_lookup = {(r.transaction_id, r.type): r for r in st_unique.itertuples()}

    results = []
    seen_tx = set()
    for r in tx_period.itertuples():
        key = (r.transaction_id, r.type)
        seen_tx.add(key)
        bank = st_lookup.get(key)
        if bank is None:
            later = st_unique[(st_unique["transaction_id"] == r.transaction_id) &
                              (st_unique["type"] == r.type) &
                              (st_unique["settlement_date"] > end)]
            if not later.empty:
                b = later.iloc[0]
                status = "Late settlement (next period)"
                bank_amount = b["amount_dec"]
                settlement_date = b["settlement_date"]
                diff = bank_amount - r.amount_dec
            else:
                status = "Missing settlement"
                bank_amount = None
                settlement_date = None
                diff = None
        else:
            bank_amount = bank.amount_dec
            settlement_date = bank.settlement_date
            diff = bank_amount - r.amount_dec
            if settlement_date > end:
                status = "Late settlement (next period)"
            elif abs(diff) <= tol:
                status = "Matched" if diff == 0 else "Matched within rounding tolerance"
            else:
                status = "Amount mismatch"
        results.append({
            "transaction_id": r.transaction_id, "type": r.type,
            "transaction_date": r.transaction_date, "transaction_amount": r.amount_dec,
            "settlement_date": settlement_date, "settlement_amount": bank_amount,
            "difference": diff, "status": status
        })

    # Bank records with no corresponding platform transaction are surfaced.
    orphan_rows = []
    for r in st_unique.itertuples():
        key = (r.transaction_id, r.type)
        if key not in tx_lookup:
            is_refund = r.type == "refund"
            orphan_rows.append({
                "transaction_id": r.transaction_id, "type": r.type,
                "transaction_date": None, "transaction_amount": None,
                "settlement_date": r.settlement_date, "settlement_amount": r.amount_dec,
                "difference": None,
                "status": "Orphan refund" if is_refund else "Unmatched bank settlement"
            })

    # Explicitly report duplicate rows separately.
    for r in duplicate_rows.itertuples():
        results.append({
            "transaction_id": r.transaction_id, "type": r.type,
            "transaction_date": tx_lookup.get((r.transaction_id, r.type)).transaction_date
                if (r.transaction_id, r.type) in tx_lookup else None,
            "transaction_amount": tx_lookup.get((r.transaction_id, r.type)).amount_dec
                if (r.transaction_id, r.type) in tx_lookup else None,
            "settlement_date": r.settlement_date, "settlement_amount": r.amount_dec,
            "difference": None, "status": "Duplicate bank settlement"
        })
    results.extend(orphan_rows)

    report = pd.DataFrame(results)
    if not report.empty:
        report["transaction_amount"] = report["transaction_amount"].map(
            lambda x: float(x) if x is not None else None)
        report["settlement_amount"] = report["settlement_amount"].map(
            lambda x: float(x) if x is not None else None)
        report["difference"] = report["difference"].map(
            lambda x: float(x) if x is not None else None)

    tx_total = sum(tx_period["amount_dec"], Decimal("0.00"))
    # Count only unique settlements that landed in the reporting month.
    st_total = sum(st_period[~st_period["duplicate_key"]]["amount_dec"], Decimal("0.00"))
    matched_total = Decimal("0.00")
    for r in tx_period.itertuples():
        b = st_lookup.get((r.transaction_id, r.type))
        if b and start <= b.settlement_date <= end:
            matched_total += min(r.amount_dec, b.amount_dec)

    counts = report["status"].value_counts().to_dict() if not report.empty else {}
    summary = {
        "period_start": str(start), "period_end": str(end),
        "platform_transaction_count": int(len(tx_period)),
        "bank_settlement_count": int(len(st_period)),
        "platform_transaction_total": float(tx_total),
        "bank_settlement_total": float(st_total),
        "matched_amount": float(matched_total),
        "gross_period_difference": float(st_total - tx_total),
        "matched_count": int(counts.get("Matched", 0) + counts.get("Matched within rounding tolerance", 0)),
        "late_settlement_count": int(counts.get("Late settlement (next period)", 0)),
        "duplicate_count": int(counts.get("Duplicate bank settlement", 0)),
        "orphan_refund_count": int(counts.get("Orphan refund", 0)),
        "missing_settlement_count": int(counts.get("Missing settlement", 0)),
        "rounding_or_amount_mismatch_count": int(counts.get("Matched within rounding tolerance", 0) + counts.get("Amount mismatch", 0)),
        "status_counts": {str(k): int(v) for k, v in counts.items()}
    }
    return report, summary

def generate_sample_data(seed: int = 42):
    """Deterministic October 2025 sample with all required planted anomalies."""
    transactions = pd.DataFrame([
        ["TXN1001", "2025-10-02", 120.00, "payment"],
        ["TXN1002", "2025-10-04", 249.99, "payment"],
        ["TXN1003", "2025-10-08", 80.00, "payment"],
        ["TXN1004", "2025-10-12", 415.50, "payment"],
        ["TXN1005", "2025-10-17", 65.25, "payment"],
        ["TXN1006", "2025-10-20", 99.99, "payment"],
        ["TXN1007", "2025-10-25", 150.00, "payment"],
        ["TXN1008", "2025-10-29", 500.00, "payment"],
        ["TXN1009", "2025-10-31", 300.00, "payment"],
        ["TXN1010", "2025-10-31", 0.10, "payment"],
        ["TXN1011", "2025-10-31", 0.10, "payment"],
        ["TXN1012", "2025-10-31", 0.10, "payment"],
    ], columns=["transaction_id", "transaction_date", "amount", "type"])
    settlements = pd.DataFrame([
        ["SET9001", "TXN1001", "2025-10-03", 120.00, "payment"],
        ["SET9002", "TXN1002", "2025-10-05", 249.99, "payment"],
        ["SET9003", "TXN1003", "2025-10-09", 80.00, "payment"],
        ["SET9004", "TXN1004", "2025-10-13", 415.50, "payment"],
        ["SET9005", "TXN1005", "2025-10-18", 65.25, "payment"],
        ["SET9006", "TXN1006", "2025-10-21", 99.98, "payment"], # one-cent rounding variance
        ["SET9007", "TXN1007", "2025-10-26", 150.00, "payment"],
        ["SET9008", "TXN1008", "2025-10-30", 500.00, "payment"],
        ["SET9009", "TXN1009", "2025-11-01", 300.00, "payment"], # next-month settlement
        ["SET9010", "TXN1010", "2025-10-31", 0.09, "payment"],
        ["SET9011", "TXN1011", "2025-10-31", 0.09, "payment"],
        ["SET9012", "TXN1012", "2025-10-31", 0.09, "payment"],
        ["SET9013", "TXN1001", "2025-10-03", 120.00, "payment"], # duplicate
        ["SET9014", "REFUND-ORPHAN-77", "2025-10-28", 25.00, "refund"], # orphan refund
    ], columns=["settlement_id", "transaction_id", "settlement_date", "amount", "type"])
    return transactions, settlements
