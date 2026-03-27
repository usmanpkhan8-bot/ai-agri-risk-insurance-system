# ============================================================
#  FILE: yield_forecast.py
#  WHAT THIS FILE DOES:
#  Predicts NEXT SEASON's yield for a district + crop
#  using historical trend analysis (Linear Regression)
#  This is your innovation — forecasting BEFORE harvest!
# ============================================================

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def forecast_yield(district, crop, seasons_ahead=1):
    """
    Predicts yield for next season based on historical trend.

    Returns:
        dict with forecasted yield, trend direction, confidence
    """

    try:
        df = pd.read_csv("outputs/crop_with_failures.csv")
    except:
        return {"error": "Run build_model.py first!"}

    # Filter for this district and crop
    subset = df[
        (df['District_Name'] == district.upper()) &
        (df['Crop'] == crop)
    ].sort_values('Crop_Year')

    if len(subset) < 3:
        return {
            "found":           False,
            "message":         f"Not enough historical data for {district} - {crop}",
            "forecasted_yield": None,
        }

    # Use year as X, yield as Y
    X = subset['Crop_Year'].values.reshape(-1, 1)
    y = subset['Yield'].values

    # Train simple linear regression on historical data
    model = LinearRegression()
    model.fit(X, y)

    # Predict next season
    last_year      = int(subset['Crop_Year'].max())
    next_year      = last_year + seasons_ahead
    forecast_input = np.array([[next_year]])
    forecasted     = round(float(model.predict(forecast_input)[0]), 2)

    # Make sure forecast is not negative
    forecasted = max(0.0, forecasted)

    # Historical average
    hist_avg = round(float(y.mean()), 2)
    hist_min = round(float(y.min()), 2)
    hist_max = round(float(y.max()), 2)

    # Trend direction
    slope = model.coef_[0]
    if slope > 0.05:
        trend   = "📈 Improving"
        t_color = "green"
    elif slope < -0.05:
        trend   = "📉 Declining"
        t_color = "red"
    else:
        trend   = "➡️ Stable"
        t_color = "orange"

    # How different is forecast from average?
    pct_change = round(((forecasted - hist_avg) / hist_avg) * 100, 1) if hist_avg > 0 else 0

    # Risk flag
    if forecasted < hist_avg * 0.75:
        forecast_risk = "HIGH — Forecasted yield is 25%+ below average"
    elif forecasted < hist_avg * 0.9:
        forecast_risk = "MEDIUM — Forecasted yield slightly below average"
    else:
        forecast_risk = "LOW — Forecasted yield is normal"

    # Historical data for chart
    history = subset[['Crop_Year', 'Yield']].tail(10).to_dict(orient='records')

    return {
        "found":            True,
        "district":         district.upper(),
        "crop":             crop,
        "last_year":        last_year,
        "next_year":        next_year,
        "forecasted_yield": forecasted,
        "hist_avg":         hist_avg,
        "hist_min":         hist_min,
        "hist_max":         hist_max,
        "pct_change":       pct_change,
        "trend":            trend,
        "trend_color":      t_color,
        "forecast_risk":    forecast_risk,
        "history":          history,
    }


# ── Test ──
if __name__ == "__main__":
    result = forecast_yield("NAMAKKAL", "Groundnut")
    if result.get("found"):
        print(f"District:          {result['district']}")
        print(f"Crop:              {result['crop']}")
        print(f"Forecasted Yield:  {result['forecasted_yield']} tons/ha for {result['next_year']}")
        print(f"Historical Avg:    {result['hist_avg']} tons/ha")
        print(f"Trend:             {result['trend']}")
        print(f"Forecast Risk:     {result['forecast_risk']}")
    else:
        print(result.get("message", "Error"))