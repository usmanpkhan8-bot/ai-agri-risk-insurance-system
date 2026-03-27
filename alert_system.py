# ============================================================
#  FILE: alert_system.py
#  WHAT THIS FILE DOES:
#  Sends automatic email alerts when a district has HIGH risk
#  Uses Gmail SMTP — free, no extra libraries needed!
#
#  SETUP (one time only):
#  1. Use a Gmail account
#  2. Go to Google Account → Security → App Passwords
#  3. Generate an App Password for "Mail"
#  4. Paste it below in EMAIL_PASSWORD
# ============================================================

import smtplib
from email.mime.text        import MIMEText
from email.mime.multipart   import MIMEMultipart
from datetime               import datetime


# ────────────────────────────────────────────
# YOUR EMAIL SETTINGS — fill these in!
# ────────────────────────────────────────────

EMAIL_SENDER   = "your_email@gmail.com"       # ← your Gmail
EMAIL_PASSWORD = "your_app_password_here"     # ← Gmail App Password
EMAIL_RECEIVER = "alert_receiver@gmail.com"   # ← who gets the alert


def send_risk_alert(district, crop, risk_score, risk_level,
                    payout_amount, weather_info=None):
    """
    Sends an email alert when crop risk is HIGH.
    Call this from app.py after risk calculation.
    """

    # Only send if risk is HIGH
    if risk_level != "HIGH":
        return {"sent": False, "reason": "Risk level not HIGH — no alert needed"}

    # Build email content
    subject = f"🚨 HIGH CROP RISK ALERT — {district} ({crop})"

    weather_section = ""
    if weather_info and weather_info.get("found"):
        weather_section = f"""
        <tr><td colspan="2" style="padding:10px 0; color:#94a3b8; font-size:13px;">
            <strong>Live Weather:</strong>
            {weather_info['temperature']}°C |
            Humidity: {weather_info['humidity']}% |
            Rainfall: {weather_info['rainfall']}mm |
            {weather_info['condition']}
        </td></tr>
        """

    html_body = f"""
    <html>
    <body style="font-family:Segoe UI,sans-serif; background:#0f1923; color:#e2e8f0; padding:30px;">

      <div style="max-width:560px; margin:0 auto; background:#1a2535;
                  border-radius:16px; padding:28px; border:1px solid #2d3f55;">

        <div style="text-align:center; margin-bottom:24px;">
          <div style="font-size:40px;">🚨</div>
          <h2 style="color:#f87171; margin:8px 0;">HIGH RISK ALERT</h2>
          <p style="color:#64748b; font-size:13px;">
            Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}
          </p>
        </div>

        <table width="100%" cellpadding="8" style="border-collapse:collapse;">
          <tr style="background:#162030;">
            <td style="color:#64748b; font-size:12px; letter-spacing:1px;">DISTRICT</td>
            <td style="color:#e2e8f0; font-weight:700;">{district}</td>
          </tr>
          <tr>
            <td style="color:#64748b; font-size:12px; letter-spacing:1px;">CROP</td>
            <td style="color:#e2e8f0; font-weight:700;">{crop}</td>
          </tr>
          <tr style="background:#162030;">
            <td style="color:#64748b; font-size:12px; letter-spacing:1px;">RISK SCORE</td>
            <td style="color:#f87171; font-weight:800; font-size:20px;">{risk_score} / 100</td>
          </tr>
          <tr>
            <td style="color:#64748b; font-size:12px; letter-spacing:1px;">RISK LEVEL</td>
            <td><span style="background:rgba(248,113,113,0.2); color:#f87171;
                             padding:4px 12px; border-radius:20px; font-weight:700;">
                HIGH RISK</span></td>
          </tr>
          <tr style="background:#162030;">
            <td style="color:#64748b; font-size:12px; letter-spacing:1px;">PAYOUT AMOUNT</td>
            <td style="color:#4ade80; font-weight:800; font-size:18px;">{payout_amount}</td>
          </tr>
          {weather_section}
        </table>

        <div style="margin-top:24px; padding:16px; background:rgba(248,113,113,0.1);
                    border-radius:10px; border:1px solid rgba(248,113,113,0.3);">
          <p style="color:#f87171; font-size:14px; margin:0;">
            ⚠️ <strong>Action Required:</strong> This district has been flagged for
            potential crop failure. Insurance payout trigger has been activated
            as per PMFBY guidelines.
          </p>
        </div>

        <p style="text-align:center; color:#334155; font-size:12px; margin-top:20px;">
          AgriInsure · AI-Based Agricultural Risk & Insurance Trigger System
        </p>
      </div>

    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECEIVER
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print(f"✅ Alert email sent to {EMAIL_RECEIVER}")
        return {"sent": True, "recipient": EMAIL_RECEIVER}

    except Exception as e:
        print(f"❌ Email failed: {e}")
        return {"sent": False, "error": str(e)}


# ── Test ──
if __name__ == "__main__":
    print("Testing alert system...")
    print("NOTE: Fill in EMAIL_SENDER and EMAIL_PASSWORD first!\n")

    result = send_risk_alert(
        district      = "NAMAKKAL",
        crop          = "Groundnut",
        risk_score    = 82.5,
        risk_level    = "HIGH",
        payout_amount = "₹28,500",
    )
    print(result)