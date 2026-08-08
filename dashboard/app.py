from pathlib import Path

import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "subscription_commerce.duckdb"

st.set_page_config(page_title="Subscription Commerce Analytics", layout="wide")
st.title("Subscription Commerce Analytics")
st.caption("Observed Olist commerce + explicitly synthetic recurring-billing analytics")

if not DB.exists():
    st.error("Warehouse not found. Run `make run` first.")
    st.stop()

con = duckdb.connect(str(DB), read_only=True)
kpi = con.execute("select * from analytics.mart_subscription_kpis").fetchdf().iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Modeled subscribers", f"{int(kpi.synthetic_subscribers):,}")
c2.metric("Synthetic churn", f"{kpi.churn_rate * 100:.1f}%")
c3.metric("Average synthetic LTV", f"R$ {kpi.avg_ltv_brl:,.0f}")
c4.metric("Synthetic recurring revenue", f"R$ {kpi.synthetic_recurring_revenue_brl:,.0f}")

st.subheader("Retention by customer value segment")
segment = con.execute("""
    select value_segment, cycle_number, retention_rate
    from analytics.mart_segment_retention
    order by value_segment, cycle_number
""").fetchdf()
pivot = segment.pivot(index="cycle_number", columns="value_segment", values="retention_rate")
st.line_chart(pivot)

st.subheader("Monthly cohort retention")
cohort = con.execute("""
    select cohort_month, cycle_number, retention_rate
    from analytics.mart_cohort_retention
    order by cohort_month, cycle_number
""").fetchdf()
selected = st.selectbox("Cohort", sorted(cohort["cohort_month"].astype(str).unique(), reverse=True))
view = cohort[cohort["cohort_month"].astype(str) == selected].set_index("cycle_number")[["retention_rate"]]
st.line_chart(view)

st.subheader("Observed revenue vs. mock marketing spend")
marketing = con.execute("""
    select month,
           sum(observed_revenue_brl) as observed_revenue_brl,
           sum(marketing_spend_brl) as mock_marketing_spend_brl
    from analytics.mart_marketing_efficiency
    group by month
    order by month
""").fetchdf().set_index("month")
st.line_chart(marketing)

st.info(
    "Subscription enrollment, billing cycles, churn, LTV, recurring revenue and retention "
    "are synthetic/model-derived. Olist order/payment/item data are observed commercial records."
)
con.close()
