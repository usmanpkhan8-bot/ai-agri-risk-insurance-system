
import pandas as pd
import os

# ────────────────────────────────────────────
# STEP 1: TELL PYTHON WHERE YOUR FILES ARE
# ────────────────────────────────────────────

# This is the path to your data folder
# Make sure your CSV files are inside the 'data' folder!
crop_file     = "data/crop_production.csv"
rainfall_file = "data/district wise rainfall normal.csv"

# ────────────────────────────────────────────
# STEP 2: LOAD THE CSV FILES
# ────────────────────────────────────────────

print("=" * 50)
print("Loading your CSV files...")
print("=" * 50)

# pd.read_csv() opens a CSV file, just like double clicking in Excel
# We store it in a variable called 'crop_df'
# df means 'dataframe' - that's just the word for a table in Python
crop_df = pd.read_csv(crop_file)

# Same thing for rainfall
rain_df = pd.read_csv(rainfall_file)

print("✅ Both files loaded successfully!\n")

# ────────────────────────────────────────────
# STEP 3: LET'S LOOK INSIDE THE FILES
# ────────────────────────────────────────────

print("=" * 50)
print("CROP PRODUCTION FILE - First 5 rows:")
print("=" * 50)
# .head(5) shows first 5 rows - like peeking at the top of Excel
print(crop_df.head(5))

print("\n")

print("=" * 50)
print("RAINFALL FILE - First 5 rows:")
print("=" * 50)
print(rain_df.head(5))

print("\n")

# ────────────────────────────────────────────
# STEP 4: CHECK THE SIZE OF YOUR DATA
# ────────────────────────────────────────────

print("=" * 50)
print("HOW BIG IS YOUR DATA?")
print("=" * 50)

# .shape tells us (number of rows, number of columns)
print(f"Crop file has:     {crop_df.shape[0]} rows and {crop_df.shape[1]} columns")
print(f"Rainfall file has: {rain_df.shape[0]} rows and {rain_df.shape[1]} columns")

print("\n")

# ────────────────────────────────────────────
# STEP 5: SEE ALL COLUMN NAMES
# ────────────────────────────────────────────

print("=" * 50)
print("COLUMN NAMES IN CROP FILE:")
print("=" * 50)
# .columns shows all column names like headers in Excel
print(list(crop_df.columns))

print("\nCOLUMN NAMES IN RAINFALL FILE:")
print(list(rain_df.columns))

print("\n")

# ────────────────────────────────────────────
# STEP 6: CHECK FOR MISSING VALUES
# ────────────────────────────────────────────

print("=" * 50)
print("MISSING VALUES IN CROP FILE:")
print("=" * 50)
# .isnull().sum() counts how many empty cells are in each column
print(crop_df.isnull().sum())

print("\nMISSING VALUES IN RAINFALL FILE:")
print(rain_df.isnull().sum())

print("\n")

# ────────────────────────────────────────────
# STEP 7: CLEAN THE DATA
# ────────────────────────────────────────────

print("=" * 50)
print("Cleaning the data...")
print("=" * 50)

# Make all district and state names UPPERCASE so they match each other
# Example: 'Tamil Nadu' and 'TAMIL NADU' become the same → 'TAMIL NADU'
crop_df['State_Name']    = crop_df['State_Name'].str.upper().str.strip()
crop_df['District_Name'] = crop_df['District_Name'].str.upper().str.strip()

rain_df['STATE_UT_NAME'] = rain_df['STATE_UT_NAME'].str.upper().str.strip()
rain_df['DISTRICT']      = rain_df['DISTRICT'].str.upper().str.strip()

# Remove rows where Production is empty (we can't use them)
# dropna means "drop rows with Not Available values"
crop_df = crop_df.dropna(subset=['Production'])

# Fill any remaining missing numbers with 0
rain_df = rain_df.fillna(0)

print("✅ Data cleaned!\n")

# ────────────────────────────────────────────
# STEP 8: FILTER ONLY THE CROPS WE CARE ABOUT
# ────────────────────────────────────────────

# We focus on common insured crops under PMFBY
target_crops = ['Groundnut', 'Rice', 'Wheat', 'Maize', 'Cotton']

# Keep only rows where Crop is in our target list
crop_df = crop_df[crop_df['Crop'].isin(target_crops)]

print(f"✅ Filtered to {len(crop_df)} rows of target crops: {target_crops}\n")

# ────────────────────────────────────────────
# STEP 9: CALCULATE YIELD PER HECTARE
# ────────────────────────────────────────────

# Yield = how much crop per hectare of land
# This is more useful than raw production numbers
# If area was 0 we avoid dividing by zero using a trick
crop_df['Yield'] = crop_df.apply(
    lambda row: round(row['Production'] / row['Area'], 2) if row['Area'] > 0 else 0,
    axis=1
)

print("✅ Yield per hectare calculated!\n")

# ────────────────────────────────────────────
# STEP 10: SAVE THE CLEANED FILE
# ────────────────────────────────────────────

# Create the outputs folder if it doesn't exist yet
os.makedirs("outputs", exist_ok=True)

# Save cleaned crop data
crop_df.to_csv("outputs/cleaned_crop_data.csv", index=False)
rain_df.to_csv("outputs/cleaned_rainfall_data.csv", index=False)

print("=" * 50)
print("✅ DONE! Cleaned files saved to outputs folder:")
print("   → outputs/cleaned_crop_data.csv")
print("   → outputs/cleaned_rainfall_data.csv")
print("=" * 50)

print("\n🎉 Step 1 complete! You're ready for Step 2.")