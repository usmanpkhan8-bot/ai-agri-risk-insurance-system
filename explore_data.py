# ============================================================
#  FILE: explore_data.py
#  WHAT THIS FILE DOES:
#  1. Loads the cleaned data we made in load_data.py
#  2. Asks important questions about the data
#  3. Finds which districts had crop failures
#  4. Saves charts as images so you can see the patterns
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt   # tool for making charts/graphs
import os

# ────────────────────────────────────────────
# STEP 1: LOAD THE CLEANED FILES
# ────────────────────────────────────────────

print("=" * 50)
print("Loading cleaned data...")
print("=" * 50)

crop_df = pd.read_csv("outputs/cleaned_crop_data.csv")
rain_df = pd.read_csv("outputs/cleaned_rainfall_data.csv")

print("✅ Loaded!\n")

# Make a folder to save our charts
os.makedirs("outputs/charts", exist_ok=True)

# ────────────────────────────────────────────
# STEP 2: BASIC SUMMARY OF THE DATA
# ────────────────────────────────────────────

print("=" * 50)
print("BASIC SUMMARY - CROP DATA")
print("=" * 50)

# .describe() gives us useful stats like min, max, average
print(crop_df[['Area', 'Production', 'Yield']].describe().round(2))

print("\n")

# How many unique districts do we have?
print(f"Total unique states:    {crop_df['State_Name'].nunique()}")
print(f"Total unique districts: {crop_df['District_Name'].nunique()}")
print(f"Years covered:          {crop_df['Crop_Year'].min()} to {crop_df['Crop_Year'].max()}")
print(f"Crops covered:          {list(crop_df['Crop'].unique())}")

print("\n")

# ────────────────────────────────────────────
# STEP 3: WHICH CROP IS GROWN THE MOST?
# ────────────────────────────────────────────

print("=" * 50)
print("TOP 5 MOST GROWN CROPS (by total production)")
print("=" * 50)

# groupby groups rows together, sum adds them up
# like a pivot table in Excel!
top_crops = crop_df.groupby('Crop')['Production'].sum().sort_values(ascending=False).head(5)
print(top_crops)
print("\n")

# ── CHART 1: Bar chart of top crops ──
plt.figure(figsize=(8, 4))
top_crops.plot(kind='bar', color='#4ade80', edgecolor='black')
plt.title('Top Crops by Total Production', fontsize=14)
plt.xlabel('Crop')
plt.ylabel('Total Production (tons)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('outputs/charts/chart1_top_crops.png')
plt.close()
print("✅ Chart 1 saved → outputs/charts/chart1_top_crops.png\n")

# ────────────────────────────────────────────
# STEP 4: HOW HAS YIELD CHANGED OVER YEARS?
# ────────────────────────────────────────────

print("=" * 50)
print("AVERAGE YIELD PER YEAR")
print("=" * 50)

yearly_yield = crop_df.groupby('Crop_Year')['Yield'].mean().round(2)
print(yearly_yield)
print("\n")

# ── CHART 2: Line chart of yield over years ──
plt.figure(figsize=(10, 4))
yearly_yield.plot(kind='line', color='#58a6ff', marker='o', linewidth=2)
plt.title('Average Crop Yield Per Year', fontsize=14)
plt.xlabel('Year')
plt.ylabel('Yield (tons per hectare)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/charts/chart2_yield_trend.png')
plt.close()
print("✅ Chart 2 saved → outputs/charts/chart2_yield_trend.png\n")

# ────────────────────────────────────────────
# STEP 5: FIND CROP FAILURE YEARS
# ────────────────────────────────────────────
# A crop failure = yield dropped more than 30% compared to average

print("=" * 50)
print("DETECTING CROP FAILURE YEARS")
print("=" * 50)

# Calculate average yield per district per crop
avg_yield = crop_df.groupby(['District_Name', 'Crop'])['Yield'].transform('mean')

# How much did yield drop compared to average?
# Negative number = dropped below average
crop_df['Yield_Drop_Pct'] = ((crop_df['Yield'] - avg_yield) / avg_yield * 100).round(2)

# Flag as failure if yield dropped more than 30%
# 1 means failure, 0 means normal
crop_df['Crop_Failure'] = (crop_df['Yield_Drop_Pct'] < -30).astype(int)

failures = crop_df[crop_df['Crop_Failure'] == 1]
print(f"Total crop failure records found: {len(failures)}")
print(f"That's {round(len(failures)/len(crop_df)*100, 1)}% of all records\n")

print("Sample failure records:")
print(failures[['State_Name', 'District_Name', 'Crop_Year', 'Crop', 'Yield', 'Yield_Drop_Pct']].head(8).to_string(index=False))
print("\n")

# ── CHART 3: Failures by year ──
failures_by_year = crop_df.groupby('Crop_Year')['Crop_Failure'].sum()

plt.figure(figsize=(10, 4))
failures_by_year.plot(kind='bar', color='#f87171', edgecolor='black')
plt.title('Number of Crop Failures Per Year', fontsize=14)
plt.xlabel('Year')
plt.ylabel('Number of Failures')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('outputs/charts/chart3_failures_by_year.png')
plt.close()
print("✅ Chart 3 saved → outputs/charts/chart3_failures_by_year.png\n")

# ────────────────────────────────────────────
# STEP 6: LOOK AT RAINFALL PATTERN
# ────────────────────────────────────────────

print("=" * 50)
print("RAINFALL SUMMARY")
print("=" * 50)
print(f"Rainfall columns: {list(rain_df.columns)}\n")

# Automatically find the annual/total column
annual_col = None
for col in rain_df.columns:
    if 'annual' in col.lower() or 'total' in col.lower():
        annual_col = col
        break

if annual_col:
    name_col = rain_df.columns[0]
    avg_rain = rain_df.groupby(name_col)[annual_col].mean().round(1).sort_values(ascending=False)
    print(f"Average rainfall by area (column used: '{annual_col}'):")
    print(avg_rain.head(10))
    print("\n")

    plt.figure(figsize=(12, 5))
    avg_rain.head(15).plot(kind='bar', color='#60a5fa', edgecolor='black')
    plt.title('Average Annual Rainfall by Area')
    plt.xlabel(name_col)
    plt.ylabel('Rainfall (mm)')
    plt.xticks(rotation=60, ha='right')
    plt.tight_layout()
    plt.savefig('outputs/charts/chart4_rainfall_by_state.png')
    plt.close()
    print("✅ Chart 4 saved → outputs/charts/chart4_rainfall_by_state.png\n")
else:
    print("⚠️  No annual column found — skipping rainfall chart. Continuing!\n")

# ────────────────────────────────────────────
# STEP 7: SAVE UPDATED CROP DATA WITH FAILURE FLAG
# ────────────────────────────────────────────

crop_df.to_csv("outputs/crop_with_failures.csv", index=False)

print("=" * 50)
print("✅ DONE! Files saved:")
print("   → outputs/crop_with_failures.csv  (has failure flag column)")
print("   → outputs/charts/  (4 charts saved as images)")
print("=" * 50)
print("\n🎉 Step 2 complete! Open outputs/charts folder to see your graphs!")