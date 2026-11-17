import streamlit as st
import pandas as pd
from reconciliation import reconcile, generate_sample_data

st.set_page_config(page_title="ClearMatch | Payment Reconciliation", page_icon="💳", layout="wide")
st.markdown("""
<style>
.main {background:#f7f8fc;}
.block-container {padding-top:2rem; max-width:1450px;}
.metric-card {background:white;padding:16px;border:1px solid #e7eaf1;border-radius:12px;}
.small-muted {color:#667085;font-size:13px;}
</style>
""", unsafe_allow_html=True)

st.title("💳 ClearMatch")
st.caption("Payment reconciliation workspace · Synthetic assessment environment")
with st.sidebar:
    st.header("Reconciliation settings")
    period_start = st.date_input("Period start", value=pd.Timestamp("2025-10-01"))
    period_end = st.date_input("Period end", value=pd.Timestamp("2025-10-31"))
    tolerance = st.number_input("Amount tolerance (₹)", min_value=0.00, value=0.01, step=0.01, format="%.2f")
    st.divider()
    st.caption("Use the included synthetic data or upload your own CSV files.")

tx_default, bank_default = generate_sample_data()
st.subheader("1. Source data")
c1, c2 = st.columns(2)
with c1:
    tx_file = st.file_uploader("Platform transactions CSV", type=["csv"], key="tx")
    transactions = pd.read_csv(tx_file) if tx_file else tx_default
    st.write(f"**{len(transactions):,} platform records**")
    st.dataframe(transactions, use_container_width=True, height=230)
with c2:
    bank_file = st.file_uploader("Bank settlements CSV", type=["csv"], key="bank")
    settlements = pd.read_csv(bank_file) if bank_file else bank_default
    st.write(f"**{len(settlements):,} bank records**")
    st.dataframe(settlements, use_container_width=True, height=230)

if st.button("Run reconciliation", type="primary", use_container_width=True):
    try:
        report, summary = reconcile(transactions, settlements, str(period_start), str(period_end), str(tolerance))
        st.session_state["report"] = report
        st.session_state["summary"] = summary
    except Exception as exc:
        st.error(f"Could not reconcile these files: {exc}")

if "report" in st.session_state:
    report, s = st.session_state["report"], st.session_state["summary"]
    st.divider()
    st.subheader("2. Reconciliation overview")
    metrics = [
        ("Platform total", f"₹{s['platform_transaction_total']:,.2f}"),
        ("Bank total", f"₹{s['bank_settlement_total']:,.2f}"),
        ("Gross difference", f"₹{s['gross_period_difference']:,.2f}"),
        ("Matched records", f"{s['matched_count']:,}"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)
    st.caption(f"Reporting window: {s['period_start']} to {s['period_end']} · "
               f"{s['platform_transaction_count']} platform transactions · "
               f"{s['bank_settlement_count']} bank records in period")
    st.subheader("3. Exceptions requiring attention")
    status_order = ["Late settlement (next period)", "Matched within rounding tolerance",
                    "Duplicate bank settlement", "Orphan refund", "Missing settlement",
                    "Amount mismatch", "Unmatched bank settlement", "Matched"]
    available = [x for x in status_order if x in report["status"].values]
    selected = st.multiselect("Filter by status", available, default=[x for x in available if x != "Matched"])
    view = report[report["status"].isin(selected)] if selected else report
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button("⬇ Download full reconciliation report",
                       report.to_csv(index=False).encode("utf-8"),
                       "reconciliation_report.csv", "text/csv")
    st.subheader("4. Exception summary")
    counts = report["status"].value_counts().rename_axis("status").reset_index(name="records")
    st.bar_chart(counts.set_index("status"))
    st.info("Interpretation: a late settlement is a timing/cut-off item, not automatically a failed payment. "
            "Duplicates are surfaced separately and excluded from the unique bank total.")
else:
    st.info("Load the sample data or upload your own CSVs, then select **Run reconciliation**.")
    st.markdown("**Included assessment scenarios:** next-month settlement · small per-row variances · duplicate bank row · orphan refund.")
