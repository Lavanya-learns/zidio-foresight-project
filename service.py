from fastapi import FastAPI, HTTPException
import pandas as pd


app = FastAPI(
    title="FORESIGHT Scoring Service",
    description="Inventory risk scoring service for NorthBay Living",
    version="1.0"
)


# Load risk data
try:

    risk_data = pd.read_csv(
        "business_risk_analysis.csv"
    )

except Exception as e:

    risk_data = pd.DataFrame()


@app.get("/")
def home():

    return {
        "service": "FORESIGHT Scoring Service",
        "status": "running",
        "description": (
            "Demand and inventory risk scoring service"
        )
    }


@app.get("/health")
def health():

    if risk_data.empty:

        return {
            "status": "error",
            "message": "Risk data could not be loaded"
        }

    return {
        "status": "healthy",
        "records_loaded": len(risk_data)
    }


@app.get("/score/{sku}")
def score_sku(sku: str):

    if risk_data.empty:

        raise HTTPException(
            status_code=500,
            detail="Risk data is not available"
        )

    sku_data = risk_data[
        risk_data["SKU"].astype(str).str.upper()
        == sku.upper()
    ].copy()

    if sku_data.empty:

        raise HTTPException(
            status_code=404,
            detail=f"SKU {sku} was not found"
        )

    # Use latest inventory snapshot
    sku_data["Snapshot_Date"] = pd.to_datetime(
        sku_data["Snapshot_Date"]
    )

    latest = sku_data.sort_values(
        "Snapshot_Date"
    ).iloc[-1]

    return {

        "SKU": latest["SKU"],

        "Snapshot_Date": (
            latest["Snapshot_Date"]
            .strftime("%Y-%m-%d")
        ),

        "Current_Stock": float(
            latest["Current_Stock"]
        ),

        "On_Order": float(
            latest["On_Order"]
        ),

        "Average_Weekly_Demand": float(
            latest["Average_Weekly_Demand"]
        ),

        "Weeks_of_Cover": float(
            latest["Weeks_of_Cover"]
        ),

        "Stockout_Risk": latest[
            "Stockout_Risk"
        ],

        "Overstock_Risk": latest[
            "Overstock_Risk"
        ],

        "Recommended_Action": latest[
            "Recommended_Action"
        ],

        "Overstock_Value": float(
            latest["Overstock_Value"]
        ),

        "Stockout_Sales_At_Risk": float(
            latest["Stockout_Sales_At_Risk"]
        ),

        "Total_Value_At_Risk": float(
            latest["Total_Value_At_Risk"]
        )
    }
