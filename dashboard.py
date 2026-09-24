import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="FORESIGHT - Inventory Risk Dashboard",
    page_icon="📊",
    layout="wide"
)


# Load data
@st.cache_data
def load_data():

    risk = pd.read_csv(
        "business_risk_analysis.csv"
    )

    sku = pd.read_csv(
        "sku_master.csv"
    )

    weekly = pd.read_csv(
        "weekly_demand.csv"
    )

    risk["Snapshot_Date"] = pd.to_datetime(
        risk["Snapshot_Date"]
    )

    weekly["Date"] = pd.to_datetime(
        weekly["Date"]
    )

    return risk, sku, weekly


try:
    risk_data, sku_master, weekly_demand = load_data()

except Exception as e:

    st.error(
        "Unable to load project data. "
        "Make sure dashboard.py is in the Zidio_Project folder."
    )

    st.stop()


# Add product information
product_info = (
    sku_master[
        [
            "SKU",
            "Product_Name",
            "Category",
            "Subcategory"
        ]
    ]
    .drop_duplicates("SKU")
)

risk_data = risk_data.merge(
    product_info,
    on="SKU",
    how="left"
)


# Title
st.title("FORESIGHT")
st.subheader(
    "Demand Forecasting & Inventory Risk Dashboard"
)

st.caption(
    "NorthBay Living | Weekly demand planning and inventory risk monitoring"
)


# Sidebar filters
st.sidebar.header("Filters")

categories = [
    "All"
] + sorted(
    risk_data["Category"]
    .dropna()
    .unique()
    .tolist()
)

selected_category = st.sidebar.selectbox(
    "Category",
    categories
)


filtered_data = risk_data.copy()

if selected_category != "All":

    filtered_data = filtered_data[
        filtered_data["Category"]
        == selected_category
    ]


skus = [
    "All"
] + sorted(
    filtered_data["SKU"]
    .dropna()
    .unique()
    .tolist()
)

selected_sku = st.sidebar.selectbox(
    "SKU",
    skus
)


if selected_sku != "All":

    filtered_data = filtered_data[
        filtered_data["SKU"]
        == selected_sku
    ]


# Latest snapshot
latest_date = filtered_data[
    "Snapshot_Date"
].max()

latest_data = filtered_data[
    filtered_data["Snapshot_Date"]
    == latest_date
].copy()


# KPI section
st.header("Inventory Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Inventory Records",
        f"{len(latest_data):,}"
    )


with col2:

    high_stockout = (
        latest_data["Stockout_Risk"]
        == "High"
    ).sum()

    st.metric(
        "High Stockout Risk",
        f"{high_stockout:,}"
    )


with col3:

    high_overstock = (
        latest_data["Overstock_Risk"]
        == "High"
    ).sum()

    st.metric(
        "High Overstock Risk",
        f"{high_overstock:,}"
    )


with col4:

    total_value = latest_data[
        "Total_Value_At_Risk"
    ].sum()

    st.metric(
        "Value at Risk",
        f"₹{total_value:,.0f}"
    )


st.divider()


# Risk summary
st.header("Risk Summary")

action_counts = (
    latest_data[
        "Recommended_Action"
    ]
    .value_counts()
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Healthy",
        int(
            action_counts.get(
                "Healthy",
                0
            )
        )
    )

with col2:

    st.metric(
        "Reorder Now",
        int(
            action_counts.get(
                "Reorder now",
                0
            )
        )
    )

with col3:

    st.metric(
        "Markdown / Clear",
        int(
            action_counts.get(
                "Markdown / clear",
                0
            )
        )
    )

with col4:

    st.metric(
        "Watch / Volatile",
        int(
            action_counts.get(
                "Watch / volatile",
                0
            )
        )
    )


st.divider()


# Priority action table
st.header("Priority Actions")

priority_data = latest_data[
    [
        "SKU",
        "Product_Name",
        "Category",
        "Current_Stock",
        "Average_Weekly_Demand",
        "Weeks_of_Cover",
        "Stockout_Risk",
        "Overstock_Risk",
        "Recommended_Action",
        "Total_Value_At_Risk"
    ]
].copy()


priority_data = priority_data.sort_values(
    "Total_Value_At_Risk",
    ascending=False
)


st.dataframe(
    priority_data,
    use_container_width=True,
    hide_index=True
)


st.divider()


# Selected SKU details
if selected_sku != "All":

    st.header(
        f"SKU Details: {selected_sku}"
    )

    sku_latest = latest_data[
        latest_data["SKU"]
        == selected_sku
    ]

    if not sku_latest.empty:

        row = sku_latest.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Current Stock",
                f"{row['Current_Stock']:,.0f}"
            )

        with col2:

            st.metric(
                "Weekly Demand",
                f"{row['Average_Weekly_Demand']:,.1f}"
            )

        with col3:

            st.metric(
                "Weeks of Cover",
                f"{row['Weeks_of_Cover']:.1f}"
            )

        with col4:

            st.metric(
                "Recommended Action",
                row["Recommended_Action"]
            )

        st.write(
            f"**Product:** {row['Product_Name']}"
        )

        st.write(
            f"**Category:** {row['Category']}"
        )

        st.write(
            f"**Subcategory:** {row['Subcategory']}"
        )

        st.write(
            f"**Stockout Risk:** {row['Stockout_Risk']}"
        )

        st.write(
            f"**Overstock Risk:** {row['Overstock_Risk']}"
        )

        st.write(
            f"**Overstock Value:** "
            f"₹{row['Overstock_Value']:,.2f}"
        )

        st.write(
            f"**Stockout Sales at Risk:** "
            f"₹{row['Stockout_Sales_At_Risk']:,.2f}"
        )


st.divider()


# Historical demand
st.header("Weekly Demand History")

if selected_sku != "All":

    history = weekly_demand[
        weekly_demand["SKU"]
        == selected_sku
    ].copy()

    history = history.sort_values(
        "Date"
    )

    if not history.empty:

        chart_data = history.set_index(
            "Date"
        )[["Units_Sold"]]

        st.line_chart(
            chart_data
        )

else:

    category_skus = filtered_data[
        "SKU"
    ].unique()

    history = weekly_demand[
        weekly_demand["SKU"]
        .isin(category_skus)
    ].copy()

    history = (
        history
        .groupby("Date")["Units_Sold"]
        .sum()
        .reset_index()
    )

    history = history.sort_values(
        "Date"
    )

    chart_data = history.set_index(
        "Date"
    )[["Units_Sold"]]

    st.line_chart(
        chart_data
    )


st.divider()


# Business impact
st.header("Business Impact")

col1, col2, col3 = st.columns(3)

with col1:

    overstock_value = latest_data[
        "Overstock_Value"
    ].sum()

    st.metric(
        "Overstock Value",
        f"₹{overstock_value:,.0f}"
    )

with col2:

    stockout_value = latest_data[
        "Stockout_Sales_At_Risk"
    ].sum()

    st.metric(
        "Stockout Sales at Risk",
        f"₹{stockout_value:,.0f}"
    )

with col3:

    total_risk = latest_data[
        "Total_Value_At_Risk"
    ].sum()

    st.metric(
        "Total Value at Risk",
        f"₹{total_risk:,.0f}"
    )


st.caption(
    f"Inventory snapshot date: "
    f"{latest_date.strftime('%Y-%m-%d')}"
)
