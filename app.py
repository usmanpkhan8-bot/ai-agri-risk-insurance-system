# ============================================================
#  FILE: app.py  (UPDATED — All 5 features + Maps + States + PDF)
# ============================================================

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import pandas as pd
import pickle
import numpy as np
import os
import json

from weather_api        import get_live_weather, DISTRICT_COORDS
from yield_forecast     import forecast_yield
from alert_system       import send_risk_alert
from premium_calculator import calculate_premium
from year_comparison    import compare_years
from pdf_export         import generate_risk_pdf

app = Flask(__name__)
app.secret_key = 'agriinsure_super_secret_key'


# ────────────────────────────────────────────
# LOAD DATA AND MODEL ONCE AT STARTUP
# ────────────────────────────────────────────

df = pd.read_csv("outputs/final_insurance_report.csv")

with open("models/xgboost_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("models/encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

districts = sorted(df['District_Name'].unique().tolist())
crops     = sorted(df['Crop'].unique().tolist())
seasons   = sorted(df['Season'].unique().tolist())

# Map logic for states to districts (required for JS frontends)
states = sorted(df['State_Name'].unique().tolist()) if 'State_Name' in df.columns else []
state_districts_map = {}
if 'State_Name' in df.columns:
    for s in states:
        state_districts_map[s] = sorted(df[df['State_Name'] == s]['District_Name'].unique().tolist())

SUM_INSURED = {
    'Rice': 45000, 'Wheat': 36000, 'Maize': 28000,
    'Groundnut': 38000, 'Cotton': 55000,
}

def format_inr(number):
    s, *d = str(int(number)).partition(".")
    r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]]) if len(s) > 3 else s
    return f"{r}"

# ────────────────────────────────────────────
# SHARED PREDICTION FUNCTION
# ────────────────────────────────────────────

def predict_risk(district, crop, season, area, yield_val):
    """Core prediction used by checker and PDF export."""

    try:    state_enc  = encoders['state'].transform(df[df['District_Name'] == district]['State_Name'].iloc[0:1])[0]
    except: state_enc  = 0
    try:    dist_enc   = encoders['district'].transform([district])[0]
    except: dist_enc   = 0
    try:    crop_enc   = encoders['crop'].transform([crop])[0]
    except: crop_enc   = 0
    try:    season_enc = encoders['season'].transform([season])[0]
    except: season_enc = 0

    hist_avg = df[(df['District_Name'] == district) & (df['Crop'] == crop)]['Yield'].mean()
    if np.isnan(hist_avg): hist_avg = df['Yield'].mean()

    avg_rainfall = df[df['District_Name'] == district]['Avg_Annual_Rainfall'].mean()
    if np.isnan(avg_rainfall): avg_rainfall = df['Avg_Annual_Rainfall'].mean()

    features   = np.array([[state_enc, dist_enc, crop_enc, season_enc,
                             2024, area, yield_val,
                             hist_avg, round(yield_val - hist_avg, 2), avg_rainfall]])
    risk_score = round(float(model.predict_proba(features)[0][1]) * 100, 1)
    risk_level = 'HIGH' if risk_score >= 70 else 'MEDIUM' if risk_score >= 40 else 'LOW'

    sum_insured = SUM_INSURED.get(crop, 35000)
    loss_pct    = abs(((yield_val - hist_avg) / hist_avg * 100)) if hist_avg > 0 and yield_val < hist_avg else 0

    if loss_pct < 25:   payout_pct, trigger = 0,   'No Trigger'
    elif loss_pct < 40: payout_pct, trigger = 25,  'Mild Loss'
    elif loss_pct < 60: payout_pct, trigger = 50,  'Moderate Loss'
    elif loss_pct < 80: payout_pct, trigger = 75,  'Severe Loss'
    else:               payout_pct, trigger = 100, 'Catastrophic Loss'

    payout_amount = round((payout_pct / 100) * sum_insured, 2)

    return {
        'district':         district,
        'crop':             crop,
        'season':           season,
        'area':             area,
        'yield_val':        yield_val,
        'hist_avg':         round(hist_avg, 2),
        'risk_score':       risk_score,
        'risk_level':       risk_level,
        'sum_insured':      f"₹{sum_insured:,}",
        'loss_pct':         round(loss_pct, 1),
        'payout_pct':       payout_pct,
        'payout_amount':    f"₹{payout_amount:,}",
        'payout_amount_raw': payout_amount,
        'trigger':          trigger,
        'eligible':         payout_amount > 0,
    }

# ────────────────────────────────────────────
# PAGE 1: HOME
# ────────────────────────────────────────────

@app.route('/')
def home():
    user_name = session.get('user_name', None)
    stats = {
        'total_records':  f"{len(df):,}",
        'eligible_count': f"{len(df[df['Payout_Amount'] > 0]):,}",
        'total_payout':   f"₹{format_inr(df['Payout_Amount'].sum())}",
        'avg_risk':       round(df['Risk_Score'].mean(), 1),
        'high_risk':      len(df[df['Risk_Level'] == 'HIGH']),
        'medium_risk':    len(df[df['Risk_Level'] == 'MEDIUM']),
        'low_risk':       len(df[df['Risk_Level'] == 'LOW']),
    }
    return render_template('index.html', stats=stats, user_name=user_name)

# ────────────────────────────────────────────
# PAGE 2: RISK CHECKER
# ────────────────────────────────────────────

@app.route('/checker', methods=['GET', 'POST'])
def checker():
    result, weather = None, None

    if request.method == 'POST':
        district  = request.form.get('district').upper().strip()
        crop      = request.form.get('crop').strip()
        season    = request.form.get('season').strip()
        area      = float(request.form.get('area', 10))
        yield_val = float(request.form.get('yield_val', 1.0))

        result  = predict_risk(district, crop, season, area, yield_val)
        weather = get_live_weather(district)

        # Auto email alert if HIGH risk
        if result['risk_level'] == 'HIGH':
            send_risk_alert(
                district      = district,
                crop          = crop,
                risk_score    = result['risk_score'],
                risk_level    = result['risk_level'],
                payout_amount = result['payout_amount'],
                weather_info  = weather,
            )

    return render_template('checker.html',
                           states=states, state_districts_map=state_districts_map,
                           districts=districts, crops=crops,
                           seasons=seasons, result=result,
                           weather=weather)

# ────────────────────────────────────────────
# PAGE 3: LOGIN
# ────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            session['user_name'] = name
            return redirect(url_for('home'))
            
    return render_template('login.html')

# ────────────────────────────────────────────
# PAGE 4: PREMIUM CALCULATOR
# ────────────────────────────────────────────

@app.route('/premium', methods=['GET', 'POST'])
def premium():
    result = None
    if request.method == 'POST':
        crop   = request.form.get('crop').strip()
        season = request.form.get('season').strip()
        area   = float(request.form.get('area', 1.0))
        result = calculate_premium(crop, season, area)

    return render_template('premium.html',
                           crops=crops, seasons=seasons,
                           result=result)

# ────────────────────────────────────────────
# PAGE 4: YEAR-OVER-YEAR COMPARISON
# ────────────────────────────────────────────

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    result          = None
    available_years = sorted(df['Crop_Year'].unique().tolist())

    if request.method == 'POST':
        district = request.form.get('district').upper().strip()
        crop     = request.form.get('crop').strip()
        year1    = int(request.form.get('year1'))
        year2    = int(request.form.get('year2'))
        result   = compare_years(district, crop, year1, year2)

    return render_template('compare.html',
                           districts=districts, crops=crops,
                           years=available_years, result=result)

# ────────────────────────────────────────────
# PAGE 5: MAP
# ────────────────────────────────────────────

@app.route('/map')
def risk_map():
    district_risks = (
        df.groupby('District_Name')
          .agg(avg_risk=('Risk_Score', 'mean'),
               total_payout=('Payout_Amount', 'sum'))
          .reset_index()
    )

    map_data = []
    for _, row in district_risks.iterrows():
        d = row['District_Name'].upper()
        if d in DISTRICT_COORDS:
            risk = round(row['avg_risk'], 1)
            map_data.append({
                'district':     row['District_Name'],
                'lat':          DISTRICT_COORDS[d]['lat'],
                'lon':          DISTRICT_COORDS[d]['lon'],
                'state':        DISTRICT_COORDS[d]['state'],
                'risk_score':   risk,
                'total_payout': f"₹{format_inr(row['total_payout'])}",
                'color':        '#f87171' if risk >= 30 else '#fbbf24' if risk >= 15 else '#4ade80',
                'risk_level':   'HIGH' if risk >= 30 else 'MEDIUM' if risk >= 15 else 'LOW',
            })

    return render_template('map.html', map_data=map_data)

# ────────────────────────────────────────────
# PAGE 6: FORECAST
# ────────────────────────────────────────────

@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    result = None
    if request.method == 'POST':
        district = request.form.get('district').upper().strip()
        crop     = request.form.get('crop').strip()
        result   = forecast_yield(district, crop)
    return render_template('forecast.html', states=states, state_districts_map=state_districts_map,
                           districts=districts, crops=crops, result=result)

# ────────────────────────────────────────────
# PAGE 7: REPORT
# ────────────────────────────────────────────

@app.route('/report')
def report():
    state_filter = request.args.get('state', 'All')
    unique_states = sorted(df['State_Name'].unique().tolist()) if 'State_Name' in df.columns else []

    filtered_df = df
    if state_filter != 'All' and 'State_Name' in df.columns:
        filtered_df = df[df['State_Name'] == state_filter]

    group_cols = ['State_Name', 'District_Name'] if 'State_Name' in filtered_df.columns else ['District_Name']
    
    district_risks = filtered_df.groupby(group_cols).agg(
        Total_Payout=('Payout_Amount', 'sum'),
        Avg_Risk_Score=('Risk_Score', 'mean'),
        Failure_Count=('Crop_Failure', 'sum')
    ).reset_index()
    
    if 'State_Name' in filtered_df.columns:
        district_risks = district_risks.sort_values(['State_Name', 'Avg_Risk_Score'], ascending=[True, False])
    else:
        district_risks = district_risks.sort_values('Avg_Risk_Score', ascending=False)
    
    rows = []
    for _, row in district_risks.iterrows():
        district_records = len(filtered_df[filtered_df['District_Name'] == row['District_Name']])
        rows.append({
            'State_Name': row['State_Name'] if 'State_Name' in dict(row) else '-',
            'District_Name': row['District_Name'],
            'Total_Payout': f"₹{format_inr(row['Total_Payout'])}",
            'Avg_Risk_Score': round(row['Avg_Risk_Score'], 1),
            'Failure_Count': int(row['Failure_Count']),
            'Total_Records': district_records
        })
    return render_template('report.html', rows=rows, states=unique_states, selected_state=state_filter)

# ────────────────────────────────────────────
# PDF DOWNLOAD ROUTE
# ────────────────────────────────────────────

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    district = request.form.get('district')
    crop     = request.form.get('crop')
    season   = request.form.get('season')
    area     = float(request.form.get('area', 1))
    yield_val= float(request.form.get('yield_val', 1))

    result  = predict_risk(district, crop, season, area, yield_val)
    weather = get_live_weather(district)

    file_path = generate_risk_pdf(result, weather)
    return send_file(file_path, as_attachment=True)

# ────────────────────────────────────────────
# CHATBOT
# ────────────────────────────────────────────

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/chatbot/ask', methods=['POST'])
def chatbot_ask():
    msg   = request.json.get('message', '').lower().strip()
    reply = get_chatbot_reply(msg)
    return jsonify({'reply': reply})

def get_chatbot_reply(msg):
    if any(w in msg for w in ['pmfby', 'scheme', 'government', 'policy']):
        return ("🌾 <b>PMFBY</b> is India's crop insurance scheme. Farmers pay a small premium "
                "(2% for Kharif, 1.5% for Rabi) and get compensated for crop damage from "
                "natural causes like drought, flood, or pest attacks.")
    elif any(w in msg for w in ['risk score', 'risk', 'score']):
        return ("📊 <b>Risk Score</b> is 0–100:<br>"
                "🟢 0–39 = LOW | 🟡 40–69 = MEDIUM | 🔴 70–100 = HIGH")
    elif any(w in msg for w in ['payout', 'money', 'compensation', 'how much']):
        return ("💰 <b>Payout slabs:</b><br>"
                "Loss &lt;25% → ₹0 | 25–40% → 25% | 40–60% → 50% | 60–80% → 75% | &gt;80% → 100%")
    elif any(w in msg for w in ['weather', 'rain', 'temperature', 'drought']):
        return ("🌦️ Weather is the biggest crop risk factor! We fetch <b>live weather</b> "
                "for your district automatically in the Risk Checker.")
    elif any(w in msg for w in ['forecast', 'predict', 'next season']):
        return ("📈 Go to the <b>Forecast</b> page! Select your district and crop "
                "to see predicted yield for next season based on historical trends.")
    elif any(w in msg for w in ['map', 'heatmap', 'zones']):
        return ("🗺️ Go to the <b>Map</b> page to see a visual heatmap of crop risk "
                "zones across India. Red = High Risk, Yellow = Medium, Green = Low.")
    elif any(w in msg for w in ['hello', 'hi', 'hey', 'namaste']):
        return ("🙏 Namaste! I'm <b>AgriBot</b>. Ask me about PMFBY, risk scores, "
                "payouts, weather, or how to use this system!")
    elif any(w in msg for w in ['how to use', 'help', 'guide']):
        return ("👋 <b>How to use AgriInsure:</b><br>"
                "1️⃣ Risk Checker → enter district + crop + yield<br>"
                "2️⃣ Get AI risk score + payout amount<br>"
                "3️⃣ Map → see India risk zones<br>"
                "4️⃣ Forecast → plan next season<br>"
                "5️⃣ Ask me anything here!")
    else:
        return ("🤔 Try asking me about: <b>PMFBY</b>, <b>risk scores</b>, "
                "<b>payouts</b>, <b>weather</b>, <b>forecast</b>, or <b>how to use</b> this system.")


if __name__ == '__main__':
    print("🌾 AgriInsure running at http://127.0.0.1:5000")
    app.run(debug=True)