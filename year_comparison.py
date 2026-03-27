# ============================================================
#  FILE: year_comparison.py
#  WHAT THIS FILE DOES:
#  Compares TWO years side by side for a district + crop
#  Shows: yield, rainfall, risk score, payout — both years
#  Great visual feature for presentations!
# ============================================================

import pandas as pd
import numpy as np


def compare_years(district, crop, year1, year2):
    """
    Compare two years side by side for a district and crop.
    Returns detailed comparison data for the UI.
    """

    try:
        df = pd.read_csv("outputs/risk_scores.csv")
    except:
        return {"error": "Run build_model.py first!"}

    try:
        rain_df = pd.read_csv("outputs/cleaned_rainfall_data.csv")
    except:
        rain_df = None

    district = district.upper().strip()

    # Filter for this district and crop
    subset = df[
        (df['District_Name'] == district) &
        (df['Crop'] == crop)
    ]

    if subset.empty:
        return {
            "found":   False,
            "message": f"No data found for {district} - {crop}"
        }

    def get_year_data(year):
        row = subset[subset['Crop_Year'] == year]
        if row.empty:
            return None
        row = row.iloc[0]

        # Get rainfall for this year if available
        rainfall = None
        if rain_df is not None:
            name_col = rain_df.columns[0]
            annual_col = next(
                (c for c in rain_df.columns if 'annual' in c.lower() or 'total' in c.lower()),
                None
            )
            if annual_col:
                rain_row = rain_df[rain_df[name_col].str.upper().str.strip() == district]
                if not rain_row.empty:
                    rainfall = round(float(rain_row[annual_col].mean()), 1)

        return {
            "year":         int(year),
            "yield":        round(float(row['Yield']), 2),
            "area":         round(float(row['Area']), 1),
            "production":   round(float(row['Production']), 1),
            "risk_score":   round(float(row.get('Risk_Score', 0)), 1),
            "risk_level":   str(row.get('Risk_Level', 'N/A')),
            "crop_failure": int(row.get('Crop_Failure', 0)),
            "yield_drop":   round(float(row.get('Yield_Drop_Pct', 0)), 1),
            "payout_amt":   round(float(row.get('Payout_Amount', 0)), 2),
            "trigger":      str(row.get('Trigger_Level', 'N/A')),
            "rainfall":     rainfall,
        }

    data1 = get_year_data(year1)
    data2 = get_year_data(year2)

    if not data1:
        return {"found": False, "message": f"No data for year {year1}"}
    if not data2:
        return {"found": False, "message": f"No data for year {year2}"}

    # Calculate differences
    yield_diff    = round(data2['yield']      - data1['yield'],      2)
    risk_diff     = round(data2['risk_score'] - data1['risk_score'], 1)
    payout_diff   = round(data2['payout_amt'] - data1['payout_amt'], 2)

    yield_change  = round((yield_diff / data1['yield'] * 100), 1) if data1['yield'] > 0 else 0
    risk_change   = round((risk_diff  / data1['risk_score'] * 100), 1) if data1['risk_score'] > 0 else 0

    # Available years for dropdowns
    available_years = sorted(
        df[df['District_Name'] == district]['Crop_Year'].unique().tolist()
    )

    return {
        "found":           True,
        "district":        district,
        "crop":            crop,
        "year1":           data1,
        "year2":           data2,
        "yield_diff":      yield_diff,
        "yield_change":    yield_change,
        "risk_diff":       risk_diff,
        "risk_change":     risk_change,
        "payout_diff":     round(payout_diff, 2),
        "available_years": available_years,
        # Summary verdict
        "verdict": (
            "improved" if yield_diff > 0 else
            "declined" if yield_diff < 0 else
            "stayed the same"
        )
    }


# ── Test ──
if __name__ == "__main__":
    result = compare_years("NAMAKKAL", "Groundnut", 2015, 2016)
    if result.get("found"):
        print(f"District: {result['district']} | Crop: {result['crop']}")
        print(f"\nYear {result['year1']['year']}:")
        print(f"  Yield:      {result['year1']['yield']} t/ha")
        print(f"  Risk Score: {result['year1']['risk_score']}")
        print(f"  Payout:     ₹{result['year1']['payout_amt']}")
        print(f"\nYear {result['year2']['year']}:")
        print(f"  Yield:      {result['year2']['yield']} t/ha")
        print(f"  Risk Score: {result['year2']['risk_score']}")
        print(f"  Payout:     ₹{result['year2']['payout_amt']}")
        print(f"\nYield {result['verdict']} by {abs(result['yield_change'])}%")
    else:
        print(result.get("message"))