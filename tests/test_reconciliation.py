import pandas as pd
import pytest
from reconciliation import reconcile, generate_sample_data, money

def test_all_four_planted_anomalies_are_detected():
    tx, bank = generate_sample_data()
    report, summary = reconcile(tx, bank)
    statuses = set(report["status"])
    assert "Late settlement (next period)" in statuses
    assert "Matched within rounding tolerance" in statuses
    assert "Duplicate bank settlement" in statuses
    assert "Orphan refund" in statuses
    assert summary["late_settlement_count"] == 1
    assert summary["duplicate_count"] == 1
    assert summary["orphan_refund_count"] == 1
    rounding_rows = report[report["status"] == "Matched within rounding tolerance"]
    assert round(rounding_rows["difference"].sum(), 2) == -0.04

def test_normal_exact_match():
    tx = pd.DataFrame([["A1", "2025-10-01", 100.00, "payment"]],
                      columns=["transaction_id","transaction_date","amount","type"])
    bank = pd.DataFrame([["S1", "A1", "2025-10-02", 100.00, "payment"]],
                        columns=["settlement_id","transaction_id","settlement_date","amount","type"])
    report, summary = reconcile(tx, bank)
    assert report.iloc[0]["status"] == "Matched"
    assert summary["gross_period_difference"] == 0.0

def test_missing_settlement_is_flagged():
    tx = pd.DataFrame([["A1", "2025-10-01", 100.00, "payment"]],
                      columns=["transaction_id","transaction_date","amount","type"])
    bank = pd.DataFrame(columns=["settlement_id","transaction_id","settlement_date","amount","type"])
    report, _ = reconcile(tx, bank)
    assert report.iloc[0]["status"] == "Missing settlement"

def test_invalid_duplicate_platform_ids_rejected():
    tx = pd.DataFrame([["A1","2025-10-01",10,"payment"],["A1","2025-10-02",10,"payment"]],
                      columns=["transaction_id","transaction_date","amount","type"])
    bank = pd.DataFrame(columns=["settlement_id","transaction_id","settlement_date","amount","type"])
    with pytest.raises(ValueError, match="duplicate transaction_id"):
        reconcile(tx, bank)

def test_money_uses_decimal_rounding():
    assert money("0.105") == money("0.11")
