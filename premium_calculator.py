# ============================================================
#  FILE: premium_calculator.py
#  WHAT THIS FILE DOES:
#  Calculates how much premium a farmer needs to PAY
#  under PMFBY (Pradhan Mantri Fasal Bima Yojana)
#
#  PMFBY PREMIUM RATES (official):
#  Kharif crops  → farmer pays 2% of sum insured
#  Rabi crops    → farmer pays 1.5% of sum insured
#  Annual crops  → farmer pays 5% of sum insured
#  Government pays the rest (called actuarial premium)
# ============================================================


# Sum insured per crop per hectare (₹) — PMFBY approximate values
SUM_INSURED = {
    'Rice':      45000,
    'Wheat':     36000,
    'Maize':     28000,
    'Groundnut': 38000,
    'Cotton':    55000,
}

# Farmer's share of premium by season (%)
FARMER_PREMIUM_RATE = {
    'Kharif':     2.0,
    'Rabi':       1.5,
    'Summer':     5.0,
    'Winter':     1.5,
    'Whole Year': 5.0,
}

# Government also pays a subsidy on top
GOVT_SUBSIDY_RATE = {
    'Kharif':     3.0,
    'Rabi':       3.5,
    'Summer':     2.0,
    'Winter':     3.5,
    'Whole Year': 2.0,
}


def calculate_premium(crop, season, area):
    """
    Calculate PMFBY insurance premium for a farmer.

    Args:
        crop    : crop name (e.g. "Rice")
        season  : season name (e.g. "Kharif")
        area    : farm area in hectares (e.g. 2.5)

    Returns:
        dict with full premium breakdown
    """

    # Get sum insured per hectare
    sum_per_hectare = SUM_INSURED.get(crop, 35000)

    # Total sum insured for farmer's area
    total_sum_insured = round(sum_per_hectare * area, 2)

    # Farmer premium rate
    farmer_rate = FARMER_PREMIUM_RATE.get(season, 2.0)
    govt_rate   = GOVT_SUBSIDY_RATE.get(season, 3.0)

    # Farmer premium amount
    farmer_premium = round((farmer_rate / 100) * total_sum_insured, 2)

    # Government subsidy amount
    govt_subsidy = round((govt_rate / 100) * total_sum_insured, 2)

    # Total actuarial premium
    total_premium = round(farmer_premium + govt_subsidy, 2)

    # Coverage ratio — how much do you get back per rupee paid?
    coverage_ratio = round(total_sum_insured / farmer_premium, 1) if farmer_premium > 0 else 0

    return {
        "crop":               crop,
        "season":             season,
        "area":               area,
        "sum_per_hectare":    f"₹{sum_per_hectare:,}",
        "total_sum_insured":  f"₹{total_sum_insured:,}",
        "farmer_rate":        farmer_rate,
        "farmer_premium":     f"₹{farmer_premium:,}",
        "farmer_premium_raw": farmer_premium,
        "govt_subsidy":       f"₹{govt_subsidy:,}",
        "total_premium":      f"₹{total_premium:,}",
        "coverage_ratio":     coverage_ratio,
        "verdict": (
            f"You pay only ₹{farmer_premium:,} to get coverage "
            f"of ₹{total_sum_insured:,}. "
            f"That's ₹{coverage_ratio} coverage per ₹1 paid!"
        )
    }


# ── Test ──
if __name__ == "__main__":
    result = calculate_premium("Rice", "Kharif", 2.5)
    for k, v in result.items():
        print(f"{k}: {v}")