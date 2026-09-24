# FORESIGHT — Demand Forecasting & Inventory Risk Analytics

A data-driven forecasting and inventory risk management project developed as part of the Zidio Development internship.

## Project Overview

FORESIGHT is designed for NorthBay Living, a direct-to-consumer home and lifestyle brand.

The project combines historical sales, SKU information, calendar data, and inventory snapshots to help operations teams:

* Forecast weekly demand at SKU level
* Identify potential stockout risks
* Identify overstock risks
* Quantify financial impact in rupees
* Prioritize inventory actions
* Explore results through an interactive dashboard
* Access SKU-level risk scoring through an API

## Business Objectives

The project addresses four key business questions:

1. What is the expected demand for each SKU?
2. Which SKUs are at risk of stockout?
3. Which SKUs have excess inventory?
4. What action should the operations team take?

## Project Structure

```text
zidio-foresight-project/
│
├── sales_daily.csv
├── sku_master.csv
├── calendar.csv
├── inventory_snapshots.csv
│
├── Zidio_Project.py
├── dashboard.py
├── service.py
├── requirements.txt
├── README.md
│
├── baseline_forecast_data.csv
├── weekly_demand.csv
├── weekly_demand_features.csv
├── model_forecast_results.csv
├── model_feature_importance.csv
├── rolling_cv_results.csv
├── rolling_cv_predictions.csv
│
├── inventory_risk_analysis.csv
├── inventory_risk_summary.csv
├── inventory_risk_by_category.csv
├── business_risk_analysis.csv
├── risk_action_summary.csv
├── clean_integrated_data.csv
│
└── Zidio_Project_Data_1.1.pdf
```

## Data

The project uses four source datasets:

* `sales_daily.csv` — daily SKU-level sales
* `sku_master.csv` — product and pricing information
* `calendar.csv` — calendar, seasonality and promotion information
* `inventory_snapshots.csv` — inventory position snapshots

The sales data contains 36,550 daily records covering January 2024 through December 2025 across 50 SKUs.

## Data Pipeline

The pipeline:

1. Loads all source datasets
2. Validates and cleans the data
3. Handles invalid SKU records in inventory data
4. Integrates sales, product, calendar and inventory information
5. Creates weekly SKU-level demand
6. Engineers lag, rolling and calendar features
7. Builds a seasonal-naive baseline
8. Trains the forecasting model
9. Performs rolling-origin cross-validation
10. Calculates inventory risk
11. Quantifies business impact
12. Produces outputs for the dashboard and scoring service

Run the main pipeline with:

```bash
python Zidio_Project.py
```

## Demand Forecasting

A Random Forest regression model is used for weekly SKU-level demand forecasting.

Features include:

* Lagged demand
* Rolling demand averages
* Rolling demand variability
* Month
* Quarter
* Week of year
* Seasonal features
* Previous-week promotion information

The model is evaluated against a seasonal-naive baseline using WAPE.

### Rolling-Origin Cross-Validation Results

The final evaluation used:

* 40 weeks initial training window
* 8-week forecast horizon
* 8-week step size
* 7 expanding-window folds

| Metric       | Model | Seasonal Naive |
| ------------ | ----: | -------------: |
| Overall WAPE | 8.60% |         16.41% |
| Overall Bias | 0.04% |         -6.21% |

The model improved WAPE by approximately **47.61%** relative to the seasonal-naive baseline across the rolling-origin evaluation.

The model outperformed the baseline in all seven evaluated folds.

## Inventory Risk Analysis

The project evaluates inventory using:

* Current stock
* On-order inventory
* Average weekly demand
* Safety stock
* Reorder point
* Lead time
* Lead-time demand
* Forward demand

### Risk Categories

**Stockout Risk**

Identifies inventory positions where available stock may not cover expected demand.

**Overstock Risk**

Identifies inventory positions where current stock substantially exceeds expected forward demand.

### Recommended Actions

The decisioning framework produces four actions:

* **Reorder now**
* **Markdown / clear**
* **Watch / volatile**
* **Healthy**

## Business Impact

The current inventory analysis covers 1,200 inventory snapshot records.

The calculated financial exposure includes:

* Overstock value: approximately ₹120.10 million
* Stockout sales at risk: approximately ₹73.35 million
* Combined calculated value at risk: approximately ₹193.45 million

These values are model-derived planning indicators based on the project's inventory and pricing assumptions.

## Dashboard

The Streamlit dashboard provides:

* Inventory overview
* Risk summary
* Priority actions
* Category filtering
* SKU filtering
* Selected SKU details
* Weekly demand history
* Business impact information

Run locally with:

```bash
streamlit run dashboard.py
```

## Scoring API

FORESIGHT also includes a FastAPI scoring service.

Run locally with:

```bash
uvicorn service:app --reload
```

Available endpoints include:

```text
GET /
GET /health
GET /score/{sku}
```

Example:

```text
/score/SKU012
```

The SKU endpoint returns the latest available inventory position, demand information, risk levels, recommended action and calculated financial impact.

The API also returns appropriate errors when risk data is unavailable or an unknown SKU is requested.

## Reproducibility

The project is designed to run from the provided source datasets.

Required Python packages are listed in:

```text
requirements.txt
```

Install dependencies with:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python Zidio_Project.py
```

The generated outputs can then be used by the dashboard and scoring service.

## Limitations

* Inventory snapshots are available monthly, while sales data is daily.
* Inventory-related fields are therefore not available for every daily sales record.
* Forecast performance is evaluated on historical data and should be monitored after deployment.
* Risk and financial-impact values depend on the inventory, pricing and demand assumptions in the source data.
* The model should be retrained periodically as new sales data becomes available.

## Technologies

* Python
* Pandas
* NumPy
* Scikit-learn
* Streamlit
* FastAPI
* Uvicorn
* Plotly

## Project Status

* Data pipeline: Complete
* Data quality and EDA: Complete
* Demand forecasting: Complete
* Rolling-origin validation: Complete
* Inventory risk scoring: Complete
* Business impact analysis: Complete
* Dashboard: Complete
* Scoring API: Complete
* Deployment: In progress

## Project Context

Developed as part of the **Zidio Development FORESIGHT internship project** for the NorthBay Living business case.
