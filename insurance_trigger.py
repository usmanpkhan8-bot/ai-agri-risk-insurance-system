# ============================================================
#  FILE: insurance_trigger.py
#  WHAT THIS FILE DOES:
#  1. Loads risk scores from build_model.py
#  2. Applies PMFBY-style payout rules
#  3. Calculates how much insurance payout each farmer gets
#  4. Generates a final insurance report
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("outputs/charts", exist_ok=True)

# ────────────────────────────────────────────
# STEP 1: LOAD RISK SCORES
# ────────────────────────────────────────────

print("=" * 50)
print("Loading risk scores...")
print("=" * 50)

df = pd.read_csv("outputs/risk_scores.csv")
print(f"✅ Loaded {len(df)} records\n")

# ────────────────────────────────────────────
# STEP 2: PMFBY PAYOUT RULES
# ────────────────────────────────────────────
# These rules are based on real PMFBY guidelines
# Sum Insured = maximum amount farmer can receive
# Payout % depends on how bad the crop loss is

# Average sum insured per crop (₹ per hectare) — PMFBY approximate values
SUM_INSURED = {
    'Rice':      45000,
    'Wheat':     36000,
    'Maize':     28000,
    'Groundnut': 38000,
    'Cotton':    55000,
}

DEFAULT_SUM_INSURED = 35000  # fallback if crop not in list above

def calculate_payout(row):
    """
    Given a row with Risk_Score and Yield_Drop_Pct,
    calculate the insurance payout amount in rupees.

    PMFBY Payout Rules:
    - Loss < 25%  → No payout (minor fluctuation, not covered)
    - Loss 25-40% → 25% of sum insured
    - Loss 40-60% → 50% of sum insured
    - Loss 60-80% → 75% of sum insured
    - Loss > 80%  → 100% of sum insured (full payout)
    """

    # Get sum insured for this crop
    sum_insured = SUM_INSURED.get(row['Crop'], DEFAULT_SUM_INSURED)

    # Use yield drop % to determine loss level
    loss_pct = abs(row['Yield_Drop_Pct']) if row['Yield_Drop_Pct'] < 0 else 0

    # Apply payout rules
    if loss_pct < 25:
        payout_pct    = 0
        trigger_level = 'No Trigger'
    elif loss_pct < 40:
        payout_pct    = 25
        trigger_level = 'Mild Loss'
    elif loss_pct < 60:
        payout_pct    = 50
        trigger_level = 'Moderate Loss'
    elif loss_pct < 80:
        payout_pct    = 75
        trigger_level = 'Severe Loss'
    else:
        payout_pct    = 100
        trigger_level = 'Catastrophic Loss'

    # If risk score is high but loss % is low,
    # we still flag it as a warning (innovation!)
    if row['Risk_Score'] >= 70 and payout_pct == 0:
        trigger_level = 'High Risk Warning ⚠️'

    payout_amount = round((payout_pct / 100) * sum_insured, 2)

    return pd.Series({
        'Sum_Insured':    sum_insured,
        'Loss_Pct':       round(loss_pct, 2),
        'Payout_Pct':     payout_pct,
        'Payout_Amount':  payout_amount,
        'Trigger_Level':  trigger_level,
    })

# ────────────────────────────────────────────
# STEP 3: APPLY RULES TO ALL RECORDS
# ────────────────────────────────────────────

print("=" * 50)
print("Calculating payouts...")
print("=" * 50)

# Apply our function to every row in the dataframe
payout_df = df.apply(calculate_payout, axis=1)

# Add new columns back to main dataframe
df = pd.concat([df, payout_df], axis=1)

print("✅ Payouts calculated!\n")

# ────────────────────────────────────────────
# STEP 4: INSURANCE DECISION
# ────────────────────────────────────────────
# Final YES/NO insurance recommendation

def insurance_decision(row):
    """
    Final insurance eligibility decision.
    Eligible if payout > 0 OR risk score is very high.
    """
    if row['Payout_Amount'] > 0:
        return 'ELIGIBLE ✅'
    elif row['Risk_Score'] >= 70:
        return 'MONITOR ⚠️'
    else:
        return 'NOT ELIGIBLE ❌'

df['Insurance_Decision'] = df.apply(insurance_decision, axis=1)

# ────────────────────────────────────────────
# STEP 5: SUMMARY REPORT
# ────────────────────────────────────────────

print("=" * 50)
print("INSURANCE TRIGGER SUMMARY")
print("=" * 50)

total         = len(df)
eligible      = len(df[df['Insurance_Decision'] == 'ELIGIBLE ✅'])
monitor       = len(df[df['Insurance_Decision'] == 'MONITOR ⚠️'])
not_eligible  = len(df[df['Insurance_Decision'] == 'NOT ELIGIBLE ❌'])
total_payout  = df['Payout_Amount'].sum()

print(f"Total records:        {total}")
print(f"ELIGIBLE for payout:  {eligible} ({round(eligible/total*100,1)}%)")
print(f"MONITOR (high risk):  {monitor}  ({round(monitor/total*100,1)}%)")
print(f"NOT ELIGIBLE:         {not_eligible} ({round(not_eligible/total*100,1)}%)")
print(f"\nTotal Payout Amount:  ₹{total_payout:,.0f}")
print(f"Average Payout:       ₹{round(df[df['Payout_Amount']>0]['Payout_Amount'].mean(), 0):,.0f}\n")

# ────────────────────────────────────────────
# STEP 6: TRIGGER LEVEL BREAKDOWN
# ────────────────────────────────────────────

print("TRIGGER LEVEL BREAKDOWN:")
print(df['Trigger_Level'].value_counts().to_string())
print("\n")

# ────────────────────────────────────────────
# STEP 7: TOP DISTRICTS NEEDING PAYOUT
# ────────────────────────────────────────────

print("=" * 50)
print("TOP 10 DISTRICTS WITH HIGHEST TOTAL PAYOUT NEEDED")
print("=" * 50)

top_districts = (df.groupby('District_Name')['Payout_Amount']
                   .sum()
                   .sort_values(ascending=False)
                   .head(10))

print(top_districts.apply(lambda x: f"₹{x:,.0f}").to_string())
print("\n")

# ── Chart 6: Top districts payout ──
plt.figure(figsize=(10, 5))
top_districts.plot(kind='bar', color='#f87171', edgecolor='black')
plt.title('Top 10 Districts by Total Insurance Payout Needed')
plt.xlabel('District')
plt.ylabel('Total Payout (₹)')
plt.xticks(rotation=60, ha='right')
plt.tight_layout()
plt.savefig('outputs/charts/chart6_top_districts.png')
plt.close()
print("✅ Chart 6 saved → chart6_top_districts.png\n")

# ── Chart 7: Trigger level pie chart ──
trigger_counts = df['Trigger_Level'].value_counts()
colors = ['#4ade80', '#facc15', '#f97316', '#f87171', '#a78bfa', '#60a5fa']

plt.figure(figsize=(7, 7))
plt.pie(trigger_counts, labels=trigger_counts.index,
        autopct='%1.1f%%', colors=colors[:len(trigger_counts)],
        startangle=140)
plt.title('Distribution of Insurance Trigger Levels')
plt.tight_layout()
plt.savefig('outputs/charts/chart7_trigger_levels.png')
plt.close()
print("✅ Chart 7 saved → chart7_trigger_levels.png\n")

# ── Chart 8: Risk Score vs Payout Amount ──
sample = df[df['Payout_Amount'] > 0].sample(min(500, len(df)), random_state=42)

plt.figure(figsize=(8, 5))
plt.scatter(sample['Risk_Score'], sample['Payout_Amount'],
            alpha=0.4, color='#a78bfa', edgecolors='none')
plt.title('Risk Score vs Payout Amount')
plt.xlabel('Risk Score (0-100)')
plt.ylabel('Payout Amount (₹)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/charts/chart8_risk_vs_payout.png')
plt.close()
print("✅ Chart 8 saved → chart8_risk_vs_payout.png\n")

# ────────────────────────────────────────────
# STEP 8: SAVE FINAL REPORT
# ────────────────────────────────────────────

# Save full report
df.to_csv("outputs/final_insurance_report.csv", index=False)

# Save only eligible records separately
eligible_df = df[df['Payout_Amount'] > 0]
eligible_df.to_csv("outputs/eligible_farmers.csv", index=False)

print("=" * 50)
print("✅ ALL DONE!")
print(f"   Eligible for payout: {eligible} records")
print(f"   Total payout needed: ₹{total_payout:,.0f}")
print("   → outputs/final_insurance_report.csv")
print("   → outputs/eligible_farmers.csv")
print("   → outputs/charts/chart6, chart7, chart8")
print("=" * 50)
print("\n🎉 insurance_trigger.py complete! Last step → dashboard.py")