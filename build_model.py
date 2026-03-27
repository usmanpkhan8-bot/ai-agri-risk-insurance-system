# ============================================================
#  FILE: build_model.py
#  WHAT THIS FILE DOES:
#  1. Prepares features for ML
#  2. Trains XGBoost model to predict crop failure
#  3. Evaluates model accuracy
#  4. Generates risk score (0-100) for each record
#  5. Saves the trained model for use in the dashboard
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import pickle  # used to save and load the trained model

from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import (accuracy_score, classification_report,
                                     confusion_matrix, roc_auc_score)
from xgboost import XGBClassifier

os.makedirs("outputs/charts", exist_ok=True)
os.makedirs("models", exist_ok=True)

# ────────────────────────────────────────────
# STEP 1: LOAD DATA
# ────────────────────────────────────────────

print("=" * 50)
print("Loading data...")
print("=" * 50)

crop_df = pd.read_csv("outputs/crop_with_failures.csv")
rain_df = pd.read_csv("outputs/cleaned_rainfall_data.csv")

print(f"✅ Crop data:     {crop_df.shape}")
print(f"✅ Rainfall data: {rain_df.shape}\n")

# ────────────────────────────────────────────
# STEP 2: PREPARE RAINFALL FEATURES
# ────────────────────────────────────────────
# We want to attach rainfall info to each crop row
# First find which column has the annual total

print("=" * 50)
print("Preparing rainfall features...")
print("=" * 50)

rain_cols = list(rain_df.columns)
print(f"Rainfall columns: {rain_cols}\n")

# Find annual column automatically
annual_col = None
for col in rain_df.columns:
    if 'annual' in col.lower() or 'total' in col.lower():
        annual_col = col
        break

# Find district/state column (first column)
name_col = rain_df.columns[0]

if annual_col:
    # Keep only name and annual columns, rename them
    rain_simple = rain_df[[name_col, annual_col]].copy()
    rain_simple.columns = ['Area_Name', 'Annual_Rainfall']

    # Get average rainfall per area
    rain_avg = rain_simple.groupby('Area_Name')['Annual_Rainfall'].mean().reset_index()
    rain_avg.columns = ['Area_Name', 'Avg_Annual_Rainfall']

    print(f"✅ Using '{annual_col}' as annual rainfall column")
    print(f"✅ Got rainfall averages for {len(rain_avg)} areas\n")
else:
    # If no annual column found, use average of all numeric columns
    numeric_cols = rain_df.select_dtypes(include=[np.number]).columns.tolist()
    rain_df['Avg_Annual_Rainfall'] = rain_df[numeric_cols].mean(axis=1)
    rain_avg = rain_df[[name_col, 'Avg_Annual_Rainfall']].copy()
    rain_avg.columns = ['Area_Name', 'Avg_Annual_Rainfall']
    print("✅ Calculated average across all months as rainfall feature\n")

# ────────────────────────────────────────────
# STEP 3: BUILD FEATURE SET
# ────────────────────────────────────────────

print("=" * 50)
print("Building features...")
print("=" * 50)

df = crop_df.copy()

# ── Encode categorical columns into numbers ──
# ML models only understand numbers, not text
le_state  = LabelEncoder()
le_dist   = LabelEncoder()
le_crop   = LabelEncoder()
le_season = LabelEncoder()

df['State_Encoded']    = le_state.fit_transform(df['State_Name'])
df['District_Encoded'] = le_dist.fit_transform(df['District_Name'])
df['Crop_Encoded']     = le_crop.fit_transform(df['Crop'])
df['Season_Encoded']   = le_season.fit_transform(df['Season'])

# ── Historical average yield per district+crop ──
df['Hist_Avg_Yield'] = df.groupby(
    ['District_Name', 'Crop'])['Yield'].transform('mean').round(2)

# ── Yield vs historical average ──
df['Yield_vs_Avg'] = (df['Yield'] - df['Hist_Avg_Yield']).round(2)

# ── Year as a feature (captures trend over time) ──
df['Year_Feature'] = df['Crop_Year']

# ── Try to merge rainfall ──
# Match by district name if possible
df['District_Upper'] = df['District_Name'].str.upper().str.strip()
rain_avg['Area_Name'] = rain_avg['Area_Name'].str.upper().str.strip()

df = df.merge(rain_avg, left_on='District_Upper',
              right_on='Area_Name', how='left')

# If no match found, fill with overall median
median_rain = rain_avg['Avg_Annual_Rainfall'].median()
df['Avg_Annual_Rainfall'] = df['Avg_Annual_Rainfall'].fillna(median_rain)

print("✅ Features built!\n")

# ────────────────────────────────────────────
# STEP 4: DEFINE FEATURES AND TARGET
# ────────────────────────────────────────────

# These are the columns we feed into the model (inputs)
features = [
    'State_Encoded',
    'District_Encoded',
    'Crop_Encoded',
    'Season_Encoded',
    'Year_Feature',
    'Area',
    'Yield',
    'Hist_Avg_Yield',
    'Yield_vs_Avg',
    'Avg_Annual_Rainfall',
]

# This is what we want the model to predict (output)
# 1 = crop failed, 0 = crop did not fail
target = 'Crop_Failure'

X = df[features]
y = df[target]

print(f"Features shape: {X.shape}")
print(f"Failure rate:   {round(y.mean()*100, 1)}% of records are failures\n")

# ────────────────────────────────────────────
# STEP 5: SPLIT INTO TRAIN AND TEST
# ────────────────────────────────────────────
# 80% of data used to TRAIN, 20% used to TEST
# test_size=0.2 means 20% for testing
# random_state=42 means results are reproducible every run

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training rows: {len(X_train)}")
print(f"Testing rows:  {len(X_test)}\n")

# ────────────────────────────────────────────
# STEP 6: TRAIN THE XGBOOST MODEL
# ────────────────────────────────────────────

print("=" * 50)
print("Training XGBoost model...")
print("=" * 50)

model = XGBClassifier(
    n_estimators=100,      # number of decision trees built
    max_depth=6,           # how deep each tree goes
    learning_rate=0.1,     # how fast the model learns
    random_state=42,
    eval_metric='logloss',
    verbosity=0,
)

model.fit(X_train, y_train)
print("✅ Model trained!\n")

# ────────────────────────────────────────────
# STEP 7: EVALUATE THE MODEL
# ────────────────────────────────────────────

print("=" * 50)
print("EVALUATING MODEL...")
print("=" * 50)

y_pred     = model.predict(X_test)
y_pred_prob = model.predict_proba(X_test)[:, 1]  # probability of failure

accuracy = accuracy_score(y_test, y_pred)
auc      = roc_auc_score(y_test, y_pred_prob)

print(f"✅ Accuracy:  {round(accuracy * 100, 2)}%")
print(f"✅ AUC Score: {round(auc, 4)}  (closer to 1.0 = better)\n")

print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=['No Failure', 'Failure']))

# ── Chart: Feature Importance ──
# Shows which features matter most to the model
importance = pd.Series(model.feature_importances_, index=features).sort_values(ascending=True)

plt.figure(figsize=(8, 5))
importance.plot(kind='barh', color='#a78bfa')
plt.title('Feature Importance — What Affects Crop Failure Most?')
plt.xlabel('Importance Score')
plt.tight_layout()
plt.savefig('outputs/charts/chart5_feature_importance.png')
plt.close()
print("✅ Chart saved → chart5_feature_importance.png\n")

# ────────────────────────────────────────────
# STEP 8: GENERATE RISK SCORE (0 to 100)
# ────────────────────────────────────────────
# Probability of failure × 100 = Risk Score
# Example: 0.73 probability → Risk Score = 73 (HIGH RISK)

print("=" * 50)
print("Generating Risk Scores...")
print("=" * 50)

df['Risk_Score'] = (model.predict_proba(X)[:, 1] * 100).round(1)

# Label the risk level based on score
def risk_label(score):
    if score >= 70:   return 'HIGH'
    elif score >= 40: return 'MEDIUM'
    else:             return 'LOW'

df['Risk_Level'] = df['Risk_Score'].apply(risk_label)

print("Risk Level Distribution:")
print(df['Risk_Level'].value_counts())
print("\nSample Risk Scores:")
print(df[['District_Name','Crop','Crop_Year','Yield',
          'Risk_Score','Risk_Level']].head(10).to_string(index=False))
print("\n")

# ────────────────────────────────────────────
# STEP 9: SAVE MODEL AND RESULTS
# ────────────────────────────────────────────

# Save the trained model as a .pkl file
# pkl = pickle file = a frozen/saved version of the model
with open("models/xgboost_model.pkl", "wb") as f:
    pickle.dump(model, f)

# Save label encoders too (we need them later in the dashboard)
with open("models/encoders.pkl", "wb") as f:
    pickle.dump({
        'state':   le_state,
        'district': le_dist,
        'crop':    le_crop,
        'season':  le_season,
    }, f)

# Save results with risk scores
df.to_csv("outputs/risk_scores.csv", index=False)

print("=" * 50)
print("✅ ALL DONE!")
print(f"   Accuracy:  {round(accuracy*100,2)}%")
print(f"   AUC Score: {round(auc,4)}")
print("   → models/xgboost_model.pkl   (trained model)")
print("   → models/encoders.pkl        (label encoders)")
print("   → outputs/risk_scores.csv    (all records with risk scores)")
print("   → outputs/charts/chart5_feature_importance.png")
print("=" * 50)
print("\n🎉 build_model.py complete! Next → insurance_trigger.py")