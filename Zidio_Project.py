from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# 1. LOAD DATASETS
sales_daily = pd.read_csv("sales_daily.csv")
sku_master = pd.read_csv("sku_master.csv")
calendar = pd.read_csv("calendar.csv")
inventory_snapshots = pd.read_csv("inventory_snapshots.csv")

print("All four datasets loaded successfully!")


# 2. CONVERT DATE COLUMNS
sales_daily["Date"] = pd.to_datetime(
    sales_daily["Date"],
    errors="coerce"
)

sku_master["Launch_Date"] = pd.to_datetime(
    sku_master["Launch_Date"],
    errors="coerce"
)

calendar["date"] = pd.to_datetime(
    calendar["date"],
    errors="coerce"
)

inventory_snapshots["Snapshot_Date"] = pd.to_datetime(
    inventory_snapshots["Snapshot_Date"],
    errors="coerce"
)

# 3. BASIC DATA QUALITY CHECK
print("\n" + "=" * 60)
print("INITIAL DATA QUALITY CHECK")
print("=" * 60)

print("\nSales shape:", sales_daily.shape)
print("SKU master shape:", sku_master.shape)
print("Calendar shape:", calendar.shape)
print("Inventory shape:", inventory_snapshots.shape)

print("\nMissing values in sales:")
print(sales_daily.isnull().sum())

print("\nMissing values in SKU master:")
print(sku_master.isnull().sum())

print("\nMissing values in calendar:")
print(calendar.isnull().sum())

print("\nMissing values in inventory:")
print(inventory_snapshots.isnull().sum())


# 4. CLEAN CALENDAR MISSING VALUES
calendar["holiday"] = calendar["holiday"].fillna(
    "No Holiday"
)

calendar["promotion_event"] = calendar[
    "promotion_event"
].fillna("No Promotion")

# 5. KEEP INVENTORY RECORDS FOR VALID SKUs
valid_skus = sku_master["SKU"].dropna().unique()

inventory_clean = inventory_snapshots[
    inventory_snapshots["SKU"].isin(valid_skus)
].copy()

print("\nValid SKUs:", len(valid_skus))
print("Inventory records after SKU filtering:",
      len(inventory_clean))

# 6. MERGE SALES WITH SKU MASTER
sales_master = sales_daily.merge(
    sku_master,
    on="SKU",
    how="left",
    validate="many_to_one"
)

print("\nSales + SKU master shape:")
print(sales_master.shape)


# 7. ADD CALENDAR INFORMATION
sales_master = sales_master.merge(
    calendar,
    left_on="Date",
    right_on="date",
    how="left",
    validate="many_to_one"
)

print("\nSales + SKU + Calendar shape:")
print(sales_master.shape)

# 8. ADD INVENTORY INFORMATION
final_data = sales_master.merge(
    inventory_clean,
    left_on=["Date", "SKU"],
    right_on=["Snapshot_Date", "SKU"],
    how="left"
)

# 9. REMOVE DUPLICATE DATE COLUMNS
final_data = final_data.drop(
    columns=["date", "Snapshot_Date"],
    errors="ignore"
)

# 10. SORT FINAL DATASET
final_data = final_data.sort_values(
    ["SKU", "Date"]
).reset_index(drop=True)

# 11. FINAL INTEGRATED DATASET CHECK
print("\n" + "=" * 60)
print("FINAL INTEGRATED DATASET")
print("=" * 60)

print("\nShape:")
print(final_data.shape)

print("\nColumns:")
print(final_data.columns.tolist())

print("\nFirst 5 rows:")
print(final_data.head())

print("\nNumber of unique SKUs:")
print(final_data["SKU"].nunique())

print("\nDate range:")
print(
    final_data["Date"].min(),
    "to",
    final_data["Date"].max()
)

print("\nMissing values:")
print(final_data.isnull().sum())

# 12. INVENTORY SNAPSHOT CHECK
print("\n" + "=" * 60)
print("INVENTORY SNAPSHOT CHECK")
print("=" * 60)

print("\nNumber of snapshot dates:")
print(
    inventory_clean["Snapshot_Date"].nunique()
)

print("\nSnapshot dates:")

print(
    inventory_clean["Snapshot_Date"]
    .drop_duplicates()
    .sort_values()
    .to_list()
)

print("\nNumber of SKUs per snapshot date:")

print(
    inventory_clean
    .groupby("Snapshot_Date")["SKU"]
    .nunique()
)

# 13. INVENTORY MERGE QUALITY
inventory_columns = [
    "Current_Stock",
    "On_Order",
    "Lead_Time_Days",
    "Safety_Stock",
    "Reorder_Point",
    "Inventory_Value"
]

existing_inventory_columns = [
    col for col in inventory_columns
    if col in final_data.columns
]

print("\n" + "=" * 60)
print("INVENTORY MERGE QUALITY")
print("=" * 60)

for column in existing_inventory_columns:

    missing_count = final_data[column].isnull().sum()

    missing_percentage = (
        missing_count / len(final_data)
    ) * 100

    print(
        f"{column}: "
        f"{missing_count} missing "
        f"({missing_percentage:.2f}%)"
    )

# 14. SAVE CLEAN INTEGRATED DATASET
final_data.to_csv(
    "clean_integrated_data.csv",
    index=False
)
print("\nClean integrated dataset saved successfully!")

# 15. BASIC DEMAND ANALYSIS
print("\n" + "=" * 60)
print("DEMAND ANALYSIS")
print("=" * 60)

total_units = final_data["Units_Sold"].sum()

print("\nTotal Units Sold:")
print(total_units)


total_revenue = final_data["Revenue"].sum()

print("\nTotal Revenue:")
print(round(total_revenue, 2))


average_daily_units = final_data["Units_Sold"].mean()

print("\nAverage Units Sold per Record:")
print(round(average_daily_units, 2))


category_sales = (
    final_data
    .groupby("Category")["Units_Sold"]
    .sum()
    .sort_values(ascending=False)
)

print("\nUnits Sold by Category:")
print(category_sales)


category_revenue = (
    final_data
    .groupby("Category")["Revenue"]
    .sum()
    .sort_values(ascending=False)
)

print("\nRevenue by Category:")
print(category_revenue)


top_skus = (
    final_data
    .groupby("SKU")["Units_Sold"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print("\nTop 10 SKUs by Units Sold:")
print(top_skus)


top_revenue_skus = (
    final_data
    .groupby("SKU")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print("\nTop 10 SKUs by Revenue:")
print(top_revenue_skus)

# 16. EDA CHART 1 — UNITS SOLD BY CATEGORY
plt.figure(figsize=(9, 5))
category_sales.plot(kind="bar")
plt.title("Total Units Sold by Category")
plt.xlabel("Category")
plt.ylabel("Units Sold")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 17. EDA CHART 2 — REVENUE BY CATEGORY
plt.figure(figsize=(9, 5))

category_revenue.plot(kind="bar")

plt.title("Total Revenue by Category")
plt.xlabel("Category")
plt.ylabel("Revenue")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 18. EDA CHART 3 — MONTHLY UNITS SOLD
monthly_sales = (
    final_data
    .groupby(
        final_data["Date"].dt.to_period("M")
    )["Units_Sold"]
    .sum()
)

plt.figure(figsize=(12, 5))

monthly_sales.plot(kind="line")

plt.title("Monthly Units Sold")
plt.xlabel("Month")
plt.ylabel("Units Sold")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 19. EDA CHART 4 — TOP 10 SKUs
plt.figure(figsize=(10, 5))

top_skus.plot(kind="bar")

plt.title("Top 10 SKUs by Units Sold")
plt.xlabel("SKU")
plt.ylabel("Units Sold")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 20. CREATE WEEKLY DEMAND
weekly_data = final_data[
    ["SKU", "Date", "Units_Sold"]
].copy()

weekly_data = weekly_data.set_index("Date")


weekly_demand = (
    weekly_data
    .groupby("SKU")["Units_Sold"]
    .resample("W-SUN")
    .sum()
    .reset_index()
)

# 21. KEEP ONLY COMPLETE WEEKS

# W-SUN means each week ends on Sunday.
# Therefore, only Monday-Sunday periods are complete.

first_date = final_data["Date"].min()
last_date = final_data["Date"].max()

first_complete_week = (
    first_date
    + pd.to_timedelta(
        6 - first_date.weekday(),
        unit="D"
    )
)

last_complete_week = (
    last_date
    - pd.to_timedelta(
        last_date.weekday() + 1,
        unit="D"
    )
)

weekly_demand = weekly_demand[
    (weekly_demand["Date"] >= first_complete_week)
    &
    (weekly_demand["Date"] <= last_complete_week)
].copy()


weekly_demand = weekly_demand.sort_values(
    ["SKU", "Date"]
).reset_index(drop=True)


# 22. WEEKLY DEMAND CHECK
print("\n" + "=" * 60)
print("WEEKLY DEMAND DATA")
print("=" * 60)

print("\nShape:")
print(weekly_demand.shape)

print("\nFirst 10 rows:")
print(weekly_demand.head(10))

print("\nNumber of SKUs:")
print(weekly_demand["SKU"].nunique())

print("\nDate range:")
print(
    weekly_demand["Date"].min(),
    "to",
    weekly_demand["Date"].max()
)

print("\nWeeks per SKU:")

print(
    weekly_demand
    .groupby("SKU")
    .size()
    .value_counts()
    .sort_index()
)

# 23. SAVE WEEKLY DEMAND
weekly_demand.to_csv(
    "weekly_demand.csv",
    index=False
)

print("\nWeekly demand dataset saved successfully!")

# 24. SEASONAL-NAIVE BASELINE
# Previous year's same week = 52 weeks earlier.

weekly_demand["Baseline_Forecast"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .shift(52)
)


baseline_data = weekly_demand.dropna(
    subset=["Baseline_Forecast"]
).copy()

# 25. BASELINE EVALUATION
baseline_error = (
    baseline_data["Units_Sold"]
    - baseline_data["Baseline_Forecast"]
)


wape_denominator = (
    baseline_data["Units_Sold"]
    .abs()
    .sum()
)

if wape_denominator != 0:

    wape = (
        baseline_error.abs().sum()
        / wape_denominator
    ) * 100

else:

    wape = np.nan


bias_denominator = (
    baseline_data["Units_Sold"].sum()
)

if bias_denominator != 0:

    bias = (
        (
            baseline_data["Baseline_Forecast"]
            - baseline_data["Units_Sold"]
        ).sum()
        / bias_denominator
    ) * 100

else:

    bias = np.nan


print("\n" + "=" * 60)
print("SEASONAL-NAIVE BASELINE")
print("=" * 60)

print("\nBaseline data shape:")
print(baseline_data.shape)

print("\nSample predictions:")

print(
    baseline_data[
        [
            "SKU",
            "Date",
            "Units_Sold",
            "Baseline_Forecast"
        ]
    ].head(10)
)

print("\nWAPE:")
print(round(wape, 2), "%")

print("\nBias:")
print(round(bias, 2), "%")


baseline_data.to_csv(
    "baseline_forecast_data.csv",
    index=False
)

print("\nBaseline data saved successfully!")

# 26. FEATURE ENGINEERING
weekly_demand = weekly_demand.sort_values(
    ["SKU", "Date"]
).reset_index(drop=True)

# Lag features
weekly_demand["Lag_1"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .shift(1)
)

weekly_demand["Lag_2"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .shift(2)
)

weekly_demand["Lag_4"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .shift(4)
)

weekly_demand["Lag_52"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .shift(52)
)

# 27. ROLLING DEMAND FEATURES
weekly_demand["Rolling_Mean_4"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .transform(
        lambda x:
        x.shift(1).rolling(4).mean()
    )
)


weekly_demand["Rolling_Mean_8"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .transform(
        lambda x:
        x.shift(1).rolling(8).mean()
    )
)


weekly_demand["Rolling_Std_4"] = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .transform(
        lambda x:
        x.shift(1).rolling(4).std()
    )
)

# 28. CALENDAR & SEASONALITY FEATURES
weekly_demand["Month"] = (
    weekly_demand["Date"].dt.month
)

weekly_demand["Quarter"] = (
    weekly_demand["Date"].dt.quarter
)

weekly_demand["Week_of_Year"] = (
    weekly_demand["Date"]
    .dt.isocalendar()
    .week
    .astype(int)
)


weekly_demand["Month_Sin"] = np.sin(
    2 * np.pi * weekly_demand["Month"] / 12
)

weekly_demand["Month_Cos"] = np.cos(
    2 * np.pi * weekly_demand["Month"] / 12
)

# 29. WEEKLY PROMOTION FEATURES
weekly_promotion = (
    sales_daily[
        ["SKU", "Date", "Promotion"]
    ]
    .set_index("Date")
    .groupby("SKU")["Promotion"]
    .resample("W-SUN")
    .max()
    .reset_index()
)


weekly_promotion = weekly_promotion[
    (weekly_promotion["Date"] >= first_complete_week)
    &
    (weekly_promotion["Date"] <= last_complete_week)
].copy()


weekly_promotion = weekly_promotion.rename(
    columns={
        "Promotion": "Weekly_Promotion"
    }
)


weekly_demand = weekly_demand.merge(
    weekly_promotion,
    on=["SKU", "Date"],
    how="left"
)


# Previous week's promotion.
# This avoids using the current week's promotion
# as a predictor of the same week's demand.

weekly_demand["Previous_Week_Promotion"] = (
    weekly_demand
    .groupby("SKU")["Weekly_Promotion"]
    .shift(1)
)

# 30. FEATURE ENGINEERING CHECK
print("\n" + "=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)

print("\nFeature columns:")

print(
    weekly_demand.columns.tolist()
)


print("\nSample feature data:")

print(
    weekly_demand[
        [
            "SKU",
            "Date",
            "Units_Sold",
            "Lag_1",
            "Lag_2",
            "Lag_4",
            "Lag_52",
            "Rolling_Mean_4",
            "Rolling_Mean_8",
            "Rolling_Std_4",
            "Month",
            "Quarter",
            "Week_of_Year",
            "Month_Sin",
            "Month_Cos",
            "Weekly_Promotion",
            "Previous_Week_Promotion"
        ]
    ].tail(10)
)

# 31. FEATURE MISSING-VALUE CHECK
feature_columns = [
    "Lag_1",
    "Lag_2",
    "Lag_4",
    "Lag_52",
    "Rolling_Mean_4",
    "Rolling_Mean_8",
    "Rolling_Std_4",
    "Weekly_Promotion",
    "Previous_Week_Promotion"
]

print("\n" + "=" * 60)
print("FEATURE MISSING VALUES")
print("=" * 60)

print(
    weekly_demand[feature_columns]
    .isnull()
    .sum()
)

# 32. SAVE MODEL-READY FEATURE DATA
weekly_demand.to_csv(
    "weekly_demand_features.csv",
    index=False
)

print(
    "\nModel-ready weekly feature dataset "
    "saved successfully!"
)

# 33. FINAL SUMMARY
print("\n" + "=" * 60)
print("FORESIGHT DATA PIPELINE COMPLETE")
print("=" * 60)

print("\nFinal integrated data shape:")
print(final_data.shape)

print("\nWeekly demand shape:")
print(weekly_demand.shape)

print("\nBaseline evaluation:")
print("WAPE:", round(wape, 2), "%")
print("Bias:", round(bias, 2), "%")

print("\nFiles created:")
print("1. clean_integrated_data.csv")
print("2. weekly_demand.csv")
print("3. baseline_forecast_data.csv")
print("4. weekly_demand_features.csv")
print("\nPipeline completed successfully!")

# M3: Modelling & Risk

print("\nM3: MODELLING & RISK")

# Select model features
model_features = [
    "Lag_1",
    "Lag_2",
    "Lag_4",
    "Rolling_Mean_4",
    "Rolling_Mean_8",
    "Rolling_Std_4",
    "Month",
    "Quarter",
    "Week_of_Year",
    "Month_Sin",
    "Month_Cos",
    "Previous_Week_Promotion"
]

model_data = weekly_demand.dropna(
    subset=model_features
).copy()

print("\nModel-ready data shape:", model_data.shape)
print("Model features:")
print(model_features)

# Encode SKU
sku_dummies = pd.get_dummies(
    model_data["SKU"],
    prefix="SKU",
    dtype=int
)

X = pd.concat(
    [
        model_data[model_features].reset_index(drop=True),
        sku_dummies.reset_index(drop=True)
    ],
    axis=1
)

y = model_data["Units_Sold"].reset_index(drop=True)

model_dates = model_data["Date"].reset_index(drop=True)
model_skus = model_data["SKU"].reset_index(drop=True)

# Create time-based train/test split
unique_dates = sorted(model_dates.unique())

split_index = int(len(unique_dates) * 0.80)

train_end_date = unique_dates[split_index - 1]
test_start_date = unique_dates[split_index]

train_mask = model_dates <= train_end_date
test_mask = model_dates >= test_start_date

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]

y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print("\nTime-based split:")
print("Training period:", train_end_date)
print("Testing period:", test_start_date)
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))

# Train Random Forest model

model = RandomForestRegressor(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("\nRandom Forest model trained successfully.")

# Generate predictions
train_predictions = model.predict(X_train)
test_predictions = model.predict(X_test)

test_predictions = np.maximum(test_predictions, 0)

# Define evaluation metrics


def calculate_wape(actual, predicted):
    denominator = np.sum(np.abs(actual))

    if denominator == 0:
        return np.nan

    return np.sum(np.abs(actual - predicted)) / denominator * 100


def calculate_bias(actual, predicted):
    denominator = np.sum(np.abs(actual))

    if denominator == 0:
        return np.nan

    return np.sum(predicted - actual) / denominator * 100


# Calculate model performance
train_wape = calculate_wape(y_train, train_predictions)
test_wape = calculate_wape(y_test, test_predictions)

train_bias = calculate_bias(y_train, train_predictions)
test_bias = calculate_bias(y_test, test_predictions)

test_mae = mean_absolute_error(y_test, test_predictions)
test_rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
test_r2 = r2_score(y_test, test_predictions)

print("\nModel Performance")
print("Training WAPE:", f"{train_wape:.2f}%")
print("Testing WAPE:", f"{test_wape:.2f}%")
print("Training Bias:", f"{train_bias:.2f}%")
print("Testing Bias:", f"{test_bias:.2f}%")
print("Test MAE:", f"{test_mae:.2f}")
print("Test RMSE:", f"{test_rmse:.2f}")
print("Test R2:", f"{test_r2:.4f}")

# Compare model with seasonal-naive baseline
model_results = pd.DataFrame({
    "SKU": model_skus.loc[test_mask].values,
    "Date": model_dates.loc[test_mask].values,
    "Actual_Units": y_test.values,
    "Model_Forecast": test_predictions
})

baseline_comparison = baseline_data[
    ["SKU", "Date", "Units_Sold", "Baseline_Forecast"]
].copy()

baseline_comparison = baseline_comparison.rename(
    columns={"Units_Sold": "Baseline_Actual"}
)

model_results = model_results.merge(
    baseline_comparison,
    on=["SKU", "Date"],
    how="left"
)

model_results["Baseline_Error"] = (
    model_results["Baseline_Actual"]
    - model_results["Baseline_Forecast"]
)

model_results["Model_Error"] = (
    model_results["Actual_Units"]
    - model_results["Model_Forecast"]
)

baseline_test = model_results.dropna(
    subset=["Baseline_Forecast"]
).copy()

baseline_wape = calculate_wape(
    baseline_test["Baseline_Actual"],
    baseline_test["Baseline_Forecast"]
)

baseline_bias = calculate_bias(
    baseline_test["Baseline_Actual"],
    baseline_test["Baseline_Forecast"]
)

print("\nModel vs Seasonal-Naive Baseline")
print("Seasonal-Naive WAPE:", f"{baseline_wape:.2f}%")
print("Random Forest WAPE:", f"{test_wape:.2f}%")
print("Seasonal-Naive Bias:", f"{baseline_bias:.2f}%")
print("Random Forest Bias:", f"{test_bias:.2f}%")

# Check for overfitting
wape_gap = test_wape - train_wape

print("\nOverfitting Check")
print("WAPE difference:", f"{wape_gap:.2f} percentage points")

if wape_gap > 10:
    print("Test error is considerably higher than training error.")
    print("This may indicate overfitting.")
else:
    print("Train and test WAPE are reasonably close.")
    print("No large train-test error gap was observed.")

# Feature importance
feature_importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": model.feature_importances_
})

feature_importance = feature_importance.sort_values(
    "Importance",
    ascending=False
)

print("\nTop 15 Model Features")
print(feature_importance.head(15).to_string(index=False))

# Feature importance chart
top_features = feature_importance.head(10).sort_values(
    "Importance"
)

plt.figure(figsize=(10, 6))

plt.barh(
    top_features["Feature"],
    top_features["Importance"]
)

plt.title("Top 10 Feature Importances - Random Forest")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.tight_layout()
plt.show()

# Actual vs predicted demand
plot_data = model_results.sort_values("Date")

daily_actual = plot_data.groupby("Date")["Actual_Units"].sum()
daily_predicted = plot_data.groupby("Date")["Model_Forecast"].sum()

plt.figure(figsize=(12, 6))

plt.plot(
    daily_actual.index,
    daily_actual.values,
    label="Actual Demand"
)

plt.plot(
    daily_predicted.index,
    daily_predicted.values,
    label="Model Forecast"
)

plt.title("Actual vs Forecasted Weekly Demand")
plt.xlabel("Date")
plt.ylabel("Units Sold")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Save model results
model_results.to_csv(
    "model_forecast_results.csv",
    index=False
)

feature_importance.to_csv(
    "model_feature_importance.csv",
    index=False
)

print("\nFiles created:")
print("1. model_forecast_results.csv")
print("2. model_feature_importance.csv")

print("\nM3 MODELLING COMPLETED")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Test WAPE:", f"{test_wape:.2f}%")
print("Test Bias:", f"{test_bias:.2f}%")
print("Test RMSE:", f"{test_rmse:.2f}")
print("Test R2:", f"{test_r2:.4f}")

# M3: INVENTORY RISK ANALYSIS

print("\n" + "=" * 60)
print("INVENTORY RISK ANALYSIS")
print("=" * 60)

# Use the original monthly inventory snapshots
risk_data = inventory_clean.copy()

# Sort data
risk_data = risk_data.sort_values(
    ["SKU", "Snapshot_Date"]
).reset_index(drop=True)

# Calculate average weekly demand for each SKU
sku_weekly_demand = (
    weekly_demand
    .groupby("SKU")["Units_Sold"]
    .mean()
    .reset_index()
)

sku_weekly_demand = sku_weekly_demand.rename(
    columns={
        "Units_Sold": "Average_Weekly_Demand"
    }
)

# Add average weekly demand to inventory snapshots
risk_data = risk_data.merge(
    sku_weekly_demand,
    on="SKU",
    how="left",
    validate="many_to_one"
)

# Estimate weeks of stock available
risk_data["Weeks_of_Cover"] = (
    risk_data["Current_Stock"]
    / risk_data["Average_Weekly_Demand"]
)

# Check whether stock is below reorder point
risk_data["Reorder_Risk"] = (
    risk_data["Current_Stock"]
    <= risk_data["Reorder_Point"]
)

# Check whether stock is below safety stock
risk_data["Safety_Stock_Risk"] = (
    risk_data["Current_Stock"]
    <= risk_data["Safety_Stock"]
)

# Estimate demand during lead time
risk_data["Lead_Time_Weeks"] = (
    risk_data["Lead_Time_Days"] / 7
)

risk_data["Lead_Time_Demand"] = (
    risk_data["Average_Weekly_Demand"]
    * risk_data["Lead_Time_Weeks"]
)

# Check whether current stock can cover lead-time demand
risk_data["Lead_Time_Risk"] = (
    risk_data["Current_Stock"]
    < risk_data["Lead_Time_Demand"]
)

# Create overall risk category
risk_data["Risk_Level"] = np.select(
    [
        risk_data["Current_Stock"]
        <= risk_data["Safety_Stock"],

        risk_data["Current_Stock"]
        <= risk_data["Reorder_Point"],

        risk_data["Current_Stock"]
        < risk_data["Lead_Time_Demand"]
    ],
    [
        "High",
        "Medium",
        "Medium"
    ],
    default="Low"
)

print("\nRisk dataset shape:")
print(risk_data.shape)

print("\nRisk level counts:")
print(
    risk_data["Risk_Level"]
    .value_counts()
)

print("\nReorder risk records:")
print(
    risk_data["Reorder_Risk"]
    .sum()
)

print("\nSafety stock risk records:")
print(
    risk_data["Safety_Stock_Risk"]
    .sum()
)

print("\nLead-time risk records:")
print(
    risk_data["Lead_Time_Risk"]
    .sum()
)

# Top risky SKUs
risk_summary = (
    risk_data
    .groupby("SKU")
    .agg(
        Average_Weekly_Demand=(
            "Average_Weekly_Demand",
            "mean"
        ),
        Average_Current_Stock=(
            "Current_Stock",
            "mean"
        ),
        Average_Weeks_of_Cover=(
            "Weeks_of_Cover",
            "mean"
        ),
        Reorder_Risk_Count=(
            "Reorder_Risk",
            "sum"
        ),
        Safety_Stock_Risk_Count=(
            "Safety_Stock_Risk",
            "sum"
        ),
        Lead_Time_Risk_Count=(
            "Lead_Time_Risk",
            "sum"
        )
    )
    .reset_index()
)

risk_summary = risk_summary.sort_values(
    "Average_Weeks_of_Cover"
)

print("\nTop 10 SKUs with lowest average stock cover:")
print(
    risk_summary
    .head(10)
    .to_string(index=False)
)

# Risk summary by category
risk_with_category = risk_data.merge(
    sku_master[
        ["SKU", "Category"]
    ],
    on="SKU",
    how="left",
    validate="many_to_one"
)

category_risk = (
    risk_with_category
    .groupby("Category")
    .agg(
        Snapshot_Count=("SKU", "count"),
        Reorder_Risk_Count=(
            "Reorder_Risk",
            "sum"
        ),
        Safety_Stock_Risk_Count=(
            "Safety_Stock_Risk",
            "sum"
        ),
        Lead_Time_Risk_Count=(
            "Lead_Time_Risk",
            "sum"
        ),
        Average_Weeks_of_Cover=(
            "Weeks_of_Cover",
            "mean"
        )
    )
    .reset_index()
)

print("\nInventory risk by category:")
print(
    category_risk
    .to_string(index=False)
)

# Save risk results
risk_data.to_csv(
    "inventory_risk_analysis.csv",
    index=False
)

risk_summary.to_csv(
    "inventory_risk_summary.csv",
    index=False
)

category_risk.to_csv(
    "inventory_risk_by_category.csv",
    index=False
)

print("\nRisk analysis files created:")
print("1. inventory_risk_analysis.csv")
print("2. inventory_risk_summary.csv")
print("3. inventory_risk_by_category.csv")

print("\nINVENTORY RISK ANALYSIS COMPLETED")

# M3: ROLLING-ORIGIN BACKTEST

print("\n" + "=" * 60)
print("ROLLING-ORIGIN BACKTEST")
print("=" * 60)

# Use the model-ready weekly data
cv_data = model_data.copy()

cv_data = cv_data.sort_values(
    ["Date", "SKU"]
).reset_index(drop=True)

# Use the same model features
cv_features = model_features.copy()

# Backtest settings
initial_train_weeks = 40
forecast_horizon = 8
step_size = 8

cv_dates = sorted(
    cv_data["Date"].unique()
)

fold_results = []
all_cv_predictions = []

fold_number = 1
train_end_index = initial_train_weeks - 1

while train_end_index + forecast_horizon < len(cv_dates):

    train_dates = cv_dates[
        :train_end_index + 1
    ]

    test_dates = cv_dates[
        train_end_index + 1:
        train_end_index + 1 + forecast_horizon
    ]

    train_fold = cv_data[
        cv_data["Date"].isin(train_dates)
    ].copy()

    test_fold = cv_data[
        cv_data["Date"].isin(test_dates)
    ].copy()

    # Create SKU encoding for this fold
    fold_train_dummies = pd.get_dummies(
        train_fold["SKU"],
        prefix="SKU",
        dtype=int
    )

    fold_test_dummies = pd.get_dummies(
        test_fold["SKU"],
        prefix="SKU",
        dtype=int
    )

    # Make sure train and test have the same SKU columns
    fold_test_dummies = fold_test_dummies.reindex(
        columns=fold_train_dummies.columns,
        fill_value=0
    )

    X_train_fold = pd.concat(
        [
            train_fold[cv_features].reset_index(drop=True),
            fold_train_dummies.reset_index(drop=True)
        ],
        axis=1
    )

    X_test_fold = pd.concat(
        [
            test_fold[cv_features].reset_index(drop=True),
            fold_test_dummies.reset_index(drop=True)
        ],
        axis=1
    )

    y_train_fold = (
        train_fold["Units_Sold"]
        .reset_index(drop=True)
    )

    y_test_fold = (
        test_fold["Units_Sold"]
        .reset_index(drop=True)
    )

    # Train model for this fold
    fold_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    fold_model.fit(
        X_train_fold,
        y_train_fold
    )

    # Predict next 8 weeks
    fold_predictions = fold_model.predict(
        X_test_fold
    )

    fold_predictions = np.maximum(
        fold_predictions,
        0
    )

    # Store predictions
    fold_prediction_data = pd.DataFrame({
        "Fold": fold_number,
        "SKU": test_fold["SKU"].values,
        "Date": test_fold["Date"].values,
        "Actual_Units": y_test_fold.values,
        "Model_Forecast": fold_predictions
    })

    # Add seasonal-naive baseline
    fold_prediction_data = fold_prediction_data.merge(
        baseline_comparison[
            [
                "SKU",
                "Date",
                "Baseline_Forecast"
            ]
        ],
        on=["SKU", "Date"],
        how="left"
    )

    fold_prediction_data["Baseline_Forecast"] = (
        fold_prediction_data["Baseline_Forecast"]
        .fillna(0)
    )

    all_cv_predictions.append(
        fold_prediction_data
    )

    # Calculate fold metrics
    fold_model_wape = calculate_wape(
        fold_prediction_data["Actual_Units"],
        fold_prediction_data["Model_Forecast"]
    )

    fold_baseline_wape = calculate_wape(
        fold_prediction_data["Actual_Units"],
        fold_prediction_data["Baseline_Forecast"]
    )

    fold_model_bias = calculate_bias(
        fold_prediction_data["Actual_Units"],
        fold_prediction_data["Model_Forecast"]
    )

    fold_baseline_bias = calculate_bias(
        fold_prediction_data["Actual_Units"],
        fold_prediction_data["Baseline_Forecast"]
    )

    fold_results.append({
        "Fold": fold_number,
        "Training_End": train_dates[-1],
        "Test_Start": test_dates[0],
        "Test_End": test_dates[-1],
        "Training_Rows": len(train_fold),
        "Test_Rows": len(test_fold),
        "Model_WAPE": fold_model_wape,
        "Baseline_WAPE": fold_baseline_wape,
        "Model_Bias": fold_model_bias,
        "Baseline_Bias": fold_baseline_bias
    })

    print(
        f"\nFold {fold_number}"
    )

    print(
        "Training:",
        train_dates[0],
        "to",
        train_dates[-1]
    )

    print(
        "Testing:",
        test_dates[0],
        "to",
        test_dates[-1]
    )

    print(
        "Model WAPE:",
        f"{fold_model_wape:.2f}%"
    )

    print(
        "Baseline WAPE:",
        f"{fold_baseline_wape:.2f}%"
    )

    # Move the origin forward
    train_end_index += step_size
    fold_number += 1


# Combine fold results
rolling_cv_results = pd.DataFrame(
    fold_results
)

rolling_cv_predictions = pd.concat(
    all_cv_predictions,
    ignore_index=True
)

# Overall CV metrics
overall_model_wape = calculate_wape(
    rolling_cv_predictions["Actual_Units"],
    rolling_cv_predictions["Model_Forecast"]
)

overall_baseline_wape = calculate_wape(
    rolling_cv_predictions["Actual_Units"],
    rolling_cv_predictions["Baseline_Forecast"]
)

overall_model_bias = calculate_bias(
    rolling_cv_predictions["Actual_Units"],
    rolling_cv_predictions["Model_Forecast"]
)

overall_baseline_bias = calculate_bias(
    rolling_cv_predictions["Actual_Units"],
    rolling_cv_predictions["Baseline_Forecast"]
)

# Calculate improvement
wape_improvement = (
    (
        overall_baseline_wape
        - overall_model_wape
    )
    / overall_baseline_wape
) * 100

print("\n" + "=" * 60)
print("ROLLING-ORIGIN CV SUMMARY")
print("=" * 60)

print("\nNumber of folds:")
print(len(rolling_cv_results))

print("\nForecast horizon:")
print(f"{forecast_horizon} weeks")

print("\nOverall Model WAPE:")
print(f"{overall_model_wape:.2f}%")

print("\nOverall Seasonal-Naive WAPE:")
print(f"{overall_baseline_wape:.2f}%")

print("\nOverall Model Bias:")
print(f"{overall_model_bias:.2f}%")

print("\nOverall Seasonal-Naive Bias:")
print(f"{overall_baseline_bias:.2f}%")

print("\nWAPE improvement over baseline:")
print(f"{wape_improvement:.2f}%")

print("\nFold-by-fold results:")
print(
    rolling_cv_results.to_string(
        index=False
    )
)

# Save rolling-origin results
rolling_cv_results.to_csv(
    "rolling_cv_results.csv",
    index=False
)

rolling_cv_predictions.to_csv(
    "rolling_cv_predictions.csv",
    index=False
)

print("\nRolling CV files created:")
print("1. rolling_cv_results.csv")
print("2. rolling_cv_predictions.csv")

print("\nROLLING-ORIGIN BACKTEST COMPLETED")

# M3: OVERSTOCK AND BUSINESS RISK

print("\n" + "=" * 60)
print("OVERSTOCK AND BUSINESS RISK")
print("=" * 60)

# Use inventory risk data
business_risk = risk_data.copy()

# Add product pricing information
product_info = (
    sku_master[
        [
            "SKU",
            "Cost_Price",
            "Selling_Price"
        ]
    ]
    .drop_duplicates("SKU")
)

business_risk = business_risk.merge(
    product_info,
    on="SKU",
    how="left",
    validate="many_to_one"
)

# Forecast demand over the forward planning window
forecast_weeks = 8

business_risk["Forward_Demand"] = (
    business_risk["Average_Weekly_Demand"]
    * forecast_weeks
)

# Expected stock after selling forecast demand
business_risk["Projected_Stock"] = (
    business_risk["Current_Stock"]
    - business_risk["Forward_Demand"]
)

# Overstock quantity
business_risk["Overstock_Units"] = np.maximum(
    business_risk["Current_Stock"]
    - business_risk["Forward_Demand"],
    0
)

# Overstock risk
business_risk["Overstock_Risk"] = np.where(
    business_risk["Overstock_Units"] > 0,
    "High",
    "Low"
)

# Stockout risk based on existing lead-time logic
business_risk["Stockout_Risk"] = np.where(
    business_risk["Risk_Level"] == "High",
    "High",
    np.where(
        business_risk["Lead_Time_Risk"],
        "Medium",
        "Low"
    )
)

# Decisioning grid


def get_action(row):

    stockout = row["Stockout_Risk"]
    overstock = row["Overstock_Risk"]

    if stockout == "High" and overstock == "Low":
        return "Reorder now"

    elif stockout == "Low" and overstock == "High":
        return "Markdown / clear"

    elif stockout == "High" and overstock == "High":
        return "Watch / volatile"

    elif stockout == "Medium":
        return "Watch / volatile"

    else:
        return "Healthy"


business_risk["Recommended_Action"] = (
    business_risk.apply(
        get_action,
        axis=1
    )
)

# Rupee value of overstock
business_risk["Overstock_Value"] = (
    business_risk["Overstock_Units"]
    * business_risk["Cost_Price"]
)

# Estimated stockout sales-at-risk
business_risk["Stockout_Units_At_Risk"] = np.maximum(
    business_risk["Lead_Time_Demand"]
    - (
        business_risk["Current_Stock"]
        + business_risk["On_Order"]
    ),
    0
)

business_risk["Stockout_Sales_At_Risk"] = (
    business_risk["Stockout_Units_At_Risk"]
    * business_risk["Selling_Price"]
)

# Combined business value at risk
business_risk["Total_Value_At_Risk"] = (
    business_risk["Overstock_Value"]
    + business_risk["Stockout_Sales_At_Risk"]
)

# Save detailed business risk output
business_risk.to_csv(
    "business_risk_analysis.csv",
    index=False
)

print("\nBusiness risk analysis shape:")
print(business_risk.shape)

print("\nRecommended actions:")
print(
    business_risk["Recommended_Action"]
    .value_counts()
)

print("\nStockout risk:")
print(
    business_risk["Stockout_Risk"]
    .value_counts()
)

print("\nOverstock risk:")
print(
    business_risk["Overstock_Risk"]
    .value_counts()
)

print("\nTotal overstock value:")
print(
    f"₹{business_risk['Overstock_Value'].sum():,.2f}"
)

print("\nTotal stockout sales at risk:")
print(
    f"₹{business_risk['Stockout_Sales_At_Risk'].sum():,.2f}"
)

print("\nTotal value at risk:")
print(
    f"₹{business_risk['Total_Value_At_Risk'].sum():,.2f}"
)

# Summary by recommended action
action_summary = (
    business_risk
    .groupby("Recommended_Action")
    .agg(
        Snapshot_Records=("SKU", "count"),
        Overstock_Value=("Overstock_Value", "sum"),
        Stockout_Sales_At_Risk=(
            "Stockout_Sales_At_Risk",
            "sum"
        ),
        Total_Value_At_Risk=(
            "Total_Value_At_Risk",
            "sum"
        )
    )
    .reset_index()
)

action_summary.to_csv(
    "risk_action_summary.csv",
    index=False
)

print("\nRisk action summary:")
print(
    action_summary.to_string(
        index=False
    )
)

print("\nFiles created:")
print("1. business_risk_analysis.csv")
print("2. risk_action_summary.csv")

print("\nOVERSTOCK AND BUSINESS RISK COMPLETED")
