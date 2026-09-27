import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="FORESIGHT | Inventory Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: #0b1220;
        color: #f4f7fb;
    }

    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #263244;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    .main-title {
        font-size: 38px;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 15px;
        margin-bottom: 28px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 5px;
    }

    .section-subtitle {
        color: #9ca3af;
        font-size: 14px;
        margin-bottom: 18px;
    }

    .kpi-card {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 14px;
        padding: 20px;
        min-height: 125px;
    }

    .kpi-label {
        color: #9ca3af;
        font-size: 13px;
        margin-bottom: 8px;
    }

    .kpi-value {
        color: #f8fafc;
        font-size: 28px;
        font-weight: 750;
    }

    .kpi-note {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 7px;
    }

    .info-box {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .risk-number {
        font-size: 26px;
        font-weight: 750;
    }

    .risk-label {
        color: #9ca3af;
        font-size: 13px;
    }

    .action-box {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 14px;
        padding: 18px;
    }

    .footer {
        text-align: center;
        color: #64748b;
        font-size: 12px;
        padding: 30px 0 10px 0;
    }

    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263244;
        padding: 15px;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #9ca3af;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    risk = pd.read_csv("business_risk_analysis.csv")
    sku = pd.read_csv("sku_master.csv")
    weekly = pd.read_csv("weekly_demand.csv")

    return risk, sku, weekly


try:
    risk_df, sku_df, weekly_df = load_data()
except Exception as e:
    st.error("The dashboard could not load the project data.")
    st.code(str(e))
    st.stop()


risk_df.columns = risk_df.columns.str.strip()
sku_df.columns = sku_df.columns.str.strip()
weekly_df.columns = weekly_df.columns.str.strip()


st.sidebar.markdown("## FORESIGHT")
st.sidebar.caption("Demand & inventory intelligence")

st.sidebar.markdown("---")

categories = ["All categories"]

if "Category" in risk_df.columns:
    category_values = sorted(
        risk_df["Category"].dropna().astype(str).unique().tolist()
    )
    categories.extend(category_values)

selected_category = st.sidebar.selectbox(
    "Category",
    categories
)

filtered_risk = risk_df.copy()

if selected_category != "All categories" and "Category" in filtered_risk.columns:
    filtered_risk = filtered_risk[
        filtered_risk["Category"].astype(str) == selected_category
    ]


sku_options = ["All SKUs"]

if "SKU" in filtered_risk.columns:
    sku_values = sorted(
        filtered_risk["SKU"].dropna().astype(str).unique().tolist()
    )
    sku_options.extend(sku_values)

selected_sku = st.sidebar.selectbox(
    "SKU",
    sku_options
)

if selected_sku != "All SKUs" and "SKU" in filtered_risk.columns:
    filtered_risk = filtered_risk[
        filtered_risk["SKU"].astype(str) == selected_sku
    ]


st.sidebar.markdown("---")
st.sidebar.caption("FORESIGHT helps turn demand signals into practical inventory decisions.")


st.markdown(
    '<div class="main-title">FORESIGHT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">A clear view of demand, inventory risk and where attention is needed.</div>',
    unsafe_allow_html=True
)


if filtered_risk.empty:
    st.warning("No records match the selected filters.")
    st.stop()


latest = filtered_risk.copy()

if "Snapshot_Date" in latest.columns:
    latest["Snapshot_Date"] = pd.to_datetime(
        latest["Snapshot_Date"],
        errors="coerce"
    )

    latest = latest.sort_values("Snapshot_Date")

    latest_date = latest["Snapshot_Date"].max()

    latest = latest[
        latest["Snapshot_Date"] == latest_date
    ]


def safe_sum(column):
    if column in latest.columns:
        return pd.to_numeric(
            latest[column],
            errors="coerce"
        ).fillna(0).sum()
    return 0


def safe_mean(column):
    if column in latest.columns:
        return pd.to_numeric(
            latest[column],
            errors="coerce"
        ).fillna(0).mean()
    return 0


stockout_value = safe_sum("Stockout_Sales_At_Risk")
overstock_value = safe_sum("Overstock_Value")
total_exposure = stockout_value + overstock_value

stockout_count = 0
overstock_count = 0

if "Stockout_Risk" in latest.columns:
    stockout_count = (
        latest["Stockout_Risk"]
        .astype(str)
        .str.lower()
        .isin(["yes", "true", "1", "high"])
        .sum()
    )

if "Overstock_Risk" in latest.columns:
    overstock_count = (
        latest["Overstock_Risk"]
        .astype(str)
        .str.lower()
        .isin(["yes", "true", "1", "high"])
        .sum()
    )


st.markdown(
    '<div class="section-title">At a glance</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">The latest inventory picture based on the selected filters.</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">SKUs in view</div>
            <div class="kpi-value">{len(latest):,}</div>
            <div class="kpi-note">Products currently being tracked</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Possible stockouts</div>
            <div class="kpi-value">{stockout_count:,}</div>
            <div class="kpi-note">Items that may need attention</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Extra stock</div>
            <div class="kpi-value">₹{overstock_value / 1e6:.2f}M</div>
            <div class="kpi-note">Capital tied up in excess inventory</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Sales at risk</div>
            <div class="kpi-value">₹{stockout_value / 1e6:.2f}M</div>
            <div class="kpi-note">Potential sales exposure from stockouts</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k5:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Total exposure</div>
            <div class="kpi-value">₹{total_exposure / 1e6:.2f}M</div>
            <div class="kpi-note">Stockout risk + excess inventory</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown(
    '<div class="section-title">What needs attention</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">A quick look at the types of inventory problems showing up right now.</div>',
    unsafe_allow_html=True
)

left, right = st.columns(2)


with left:
    risk_counts = pd.DataFrame({
        "Risk": ["Stockout", "Overstock"],
        "SKUs": [stockout_count, overstock_count]
    })

    fig = px.bar(
        risk_counts,
        x="Risk",
        y="SKUs",
        text="SKUs",
        title="Items that may need attention"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        height=360,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with right:
    financial_data = pd.DataFrame({
        "Area": [
            "Sales at risk",
            "Extra stock"
        ],
        "Value": [
            stockout_value,
            overstock_value
        ]
    })

    fig = px.bar(
        financial_data,
        x="Area",
        y="Value",
        text="Value",
        title="Where money is currently exposed"
    )

    fig.update_traces(
        texttemplate="₹%{y:.2s}",
        textposition="outside"
    )

    fig.update_layout(
        height=360,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
        yaxis_title="Value (₹)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


if "Recommended_Action" in latest.columns:

    st.markdown(
        '<div class="section-title">Suggested actions</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">These actions are based on the current risk signals in the data.</div>',
        unsafe_allow_html=True
    )

    action_counts = (
        latest["Recommended_Action"]
        .fillna("Review")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    action_counts.columns = ["Action", "SKUs"]

    fig = px.bar(
        action_counts,
        x="SKUs",
        y="Action",
        orientation="h",
        text="SKUs",
        title="What the model is suggesting"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        height=400,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=40, t=60, b=20),
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


if "Category" in latest.columns:

    st.markdown(
        '<div class="section-title">Risk by category</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">See where the largest inventory exposure is concentrated.</div>',
        unsafe_allow_html=True
    )

    category_data = (
        latest.groupby("Category", dropna=False)
        .agg(
            Stockout_Risk=("Stockout_Sales_At_Risk", "sum"),
            Overstock=("Overstock_Value", "sum")
        )
        .reset_index()
    )

    category_long = category_data.melt(
        id_vars="Category",
        value_vars=["Stockout_Risk", "Overstock"],
        var_name="Risk_Type",
        value_name="Value"
    )

    category_long["Risk_Type"] = category_long["Risk_Type"].replace({
        "Stockout_Risk": "Sales at risk",
        "Overstock": "Extra stock"
    })

    fig = px.bar(
        category_long,
        x="Category",
        y="Value",
        color="Risk_Type",
        barmode="group",
        title="Financial exposure by category"
    )

    fig.update_layout(
        height=430,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=80),
        yaxis_title="Value (₹)",
        xaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.markdown(
    '<div class="section-title">Priority list</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">The SKUs with the biggest financial impact are shown first.</div>',
    unsafe_allow_html=True
)

priority_df = latest.copy()

if "Total_Value_At_Risk" in priority_df.columns:
    priority_df = priority_df.sort_values(
        "Total_Value_At_Risk",
        ascending=False
    )

display_columns = [
    "SKU",
    "Category",
    "Current_Stock",
    "Average_Weekly_Demand",
    "Weeks_of_Cover",
    "Stockout_Risk",
    "Overstock_Risk",
    "Recommended_Action",
    "Total_Value_At_Risk"
]

available_columns = [
    column for column in display_columns
    if column in priority_df.columns
]

if available_columns:
    table_df = priority_df[available_columns].head(15).copy()

    rename_map = {
        "SKU": "SKU",
        "Category": "Category",
        "Current_Stock": "Current stock",
        "Average_Weekly_Demand": "Weekly demand",
        "Weeks_of_Cover": "Weeks of cover",
        "Stockout_Risk": "Stockout risk",
        "Overstock_Risk": "Overstock risk",
        "Recommended_Action": "Suggested action",
        "Total_Value_At_Risk": "Value at risk"
    }

    table_df = table_df.rename(columns=rename_map)

    if "Value at risk" in table_df.columns:
        table_df["Value at risk"] = table_df["Value at risk"].apply(
            lambda x: f"₹{x:,.0f}" if pd.notna(x) else "₹0"
        )

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True
    )


st.markdown(
    '<div class="section-title">SKU details</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Choose a product to understand its current position and demand pattern.</div>',
    unsafe_allow_html=True
)

if "SKU" in risk_df.columns:

    sku_list = sorted(
        risk_df["SKU"].dropna().astype(str).unique().tolist()
    )

    detail_sku = st.selectbox(
        "Select a SKU",
        sku_list,
        key="detail_sku"
    )

    sku_detail = risk_df[
        risk_df["SKU"].astype(str) == detail_sku
    ].copy()

    if not sku_detail.empty:

        detail = sku_detail.iloc[-1]

        d1, d2, d3, d4 = st.columns(4)

        with d1:
            value = detail.get("Current_Stock", 0)
            st.metric(
                "Current stock",
                f"{value:,.0f}" if pd.notna(value) else "0"
            )

        with d2:
            value = detail.get("Average_Weekly_Demand", 0)
            st.metric(
                "Weekly demand",
                f"{value:,.1f}" if pd.notna(value) else "0"
            )

        with d3:
            value = detail.get("Weeks_of_Cover", 0)
            st.metric(
                "Weeks of cover",
                f"{value:.1f}" if pd.notna(value) else "0"
            )

        with d4:
            action = detail.get(
                "Recommended_Action",
                "Review"
            )
            st.metric(
                "Suggested action",
                str(action)
            )


        if "SKU" in weekly_df.columns:

            sku_weekly = weekly_df[
                weekly_df["SKU"].astype(str) == detail_sku
            ].copy()

            if not sku_weekly.empty:

                date_column = None

                for candidate in [
                    "Week",
                    "Week_Start",
                    "Date",
                    "week_start",
                    "date"
                ]:
                    if candidate in sku_weekly.columns:
                        date_column = candidate
                        break

                demand_column = None

                for candidate in [
                    "Weekly_Demand",
                    "Demand",
                    "Actual_Demand",
                    "y"
                ]:
                    if candidate in sku_weekly.columns:
                        demand_column = candidate
                        break

                if date_column and demand_column:

                    sku_weekly[date_column] = pd.to_datetime(
                        sku_weekly[date_column],
                        errors="coerce"
                    )

                    sku_weekly[demand_column] = pd.to_numeric(
                        sku_weekly[demand_column],
                        errors="coerce"
                    )

                    sku_weekly = sku_weekly.dropna(
                        subset=[date_column, demand_column]
                    )

                    fig = px.area(
                        sku_weekly,
                        x=date_column,
                        y=demand_column,
                        title=f"How demand has moved for {detail_sku}"
                    )

                    fig.update_layout(
                        height=400,
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=20, r=20, t=60, b=20),
                        xaxis_title="",
                        yaxis_title="Demand"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


st.markdown(
    '<div class="section-title">Overall demand</div>',
    unsafe_allow_html=True
)

if not weekly_df.empty:

    date_column = None

    for candidate in [
        "Week",
        "Week_Start",
        "Date",
        "week_start",
        "date"
    ]:
        if candidate in weekly_df.columns:
            date_column = candidate
            break

    demand_column = None

    for candidate in [
        "Weekly_Demand",
        "Demand",
        "Actual_Demand",
        "y"
    ]:
        if candidate in weekly_df.columns:
            demand_column = candidate
            break

    if date_column and demand_column:

        demand_view = weekly_df.copy()

        demand_view[date_column] = pd.to_datetime(
            demand_view[date_column],
            errors="coerce"
        )

        demand_view[demand_column] = pd.to_numeric(
            demand_view[demand_column],
            errors="coerce"
        )

        demand_view = demand_view.dropna(
            subset=[date_column, demand_column]
        )

        overall_demand = (
            demand_view.groupby(date_column)[demand_column]
            .sum()
            .reset_index()
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=overall_demand[date_column],
                y=overall_demand[demand_column],
                mode="lines",
                fill="tozeroy",
                name="Demand"
            )
        )

        fig.update_layout(
            title="Weekly demand across all products",
            height=430,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis_title="",
            yaxis_title="Demand"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


with st.expander("How to read this dashboard"):

    st.markdown("""
    **Stockout risk** means the available inventory may not be enough to support expected demand.

    **Overstock risk** highlights products where inventory is considerably higher than the expected demand.

    **Sales at risk** estimates the potential sales exposure associated with stockout situations.

    **Extra stock** represents the value tied up in inventory that may be higher than needed.

    **Suggested action** gives a practical next step based on the risk signals in the project data.

    The dashboard is intended to support inventory decisions by bringing demand, stock levels and financial impact together in one place.
    """)


st.markdown(
    """
    <div class="footer">
        FORESIGHT · Demand Forecasting & Inventory Risk Analytics
    </div>
    """,
    unsafe_allow_html=True
)
