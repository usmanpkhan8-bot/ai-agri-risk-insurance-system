# ============================================================
#  FILE: pdf_export.py
#  WHAT THIS FILE DOES:
#  Generates a downloadable PDF report for the farmer
#  showing their risk score, payout amount, and details
#  Farmer can print this and take it to the bank/insurance office
#
#  REQUIRES: pip install reportlab
# ============================================================

from reportlab.lib.pagesizes  import A4
from reportlab.lib            import colors
from reportlab.lib.styles     import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units      import cm
from reportlab.platypus       import (SimpleDocTemplate, Paragraph, Spacer,
                                      Table, TableStyle, HRFlowable)
from reportlab.lib.enums      import TA_CENTER, TA_LEFT
from datetime                 import datetime
import os


def generate_risk_pdf(result, weather=None, output_path="outputs/risk_report.pdf"):
    """
    Generates a PDF risk report for a farmer.

    Args:
        result      : dict from predict_risk() in app.py
        weather     : dict from get_live_weather() (optional)
        output_path : where to save the PDF

    Returns:
        output_path if successful
    """

    os.makedirs("outputs", exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )

    # ── Colors ──
    GREEN  = colors.HexColor("#16a34a")
    RED    = colors.HexColor("#dc2626")
    YELLOW = colors.HexColor("#d97706")
    DARK   = colors.HexColor("#0f172a")
    GREY   = colors.HexColor("#64748b")
    WHITE  = colors.white
    LIGHT  = colors.HexColor("#f0fdf4")

    risk_color = RED if result['risk_level'] == 'HIGH' else \
                 YELLOW if result['risk_level'] == 'MEDIUM' else GREEN

    # ── Styles ──
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title', fontSize=18, fontName='Helvetica-Bold',
        textColor=GREEN, alignment=TA_CENTER, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', fontSize=11, fontName='Helvetica',
        textColor=GREY, alignment=TA_CENTER, spaceAfter=2,
    )
    section_style = ParagraphStyle(
        'Section', fontSize=10, fontName='Helvetica-Bold',
        textColor=DARK, spaceBefore=12, spaceAfter=6,
    )
    normal_style = ParagraphStyle(
        'Normal2', fontSize=9, fontName='Helvetica',
        textColor=DARK, spaceAfter=3,
    )
    small_style = ParagraphStyle(
        'Small', fontSize=8, fontName='Helvetica',
        textColor=GREY, alignment=TA_CENTER,
    )

    story = []

    # ── Header ──
    story.append(Paragraph("🌾 AgriInsure", title_style))
    story.append(Paragraph("AI-Based Agricultural Risk & Insurance Report", subtitle_style))
    story.append(Paragraph("Aligned with Pradhan Mantri Fasal Bima Yojana (PMFBY)", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN))
    story.append(Spacer(1, 0.4*cm))

    # ── Report metadata ──
    meta_data = [
        ["Report Generated:", datetime.now().strftime("%d %B %Y, %I:%M %p")],
        ["District:",         result['district']],
        ["Crop:",             result['crop']],
        ["Farm Area:",        f"{result['area']} hectares"],
        ["Season:",           result.get('season', 'N/A')],
    ]
    meta_table = Table(meta_data, colWidths=[5*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), GREY),
        ('TEXTCOLOR', (1,0), (1,-1), DARK),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.4*cm))

    # ── Risk Score (big centered) ──
    story.append(Paragraph("RISK ASSESSMENT", section_style))

    risk_data = [[
        f"Risk Score\n{result['risk_score']} / 100",
        f"Risk Level\n{result['risk_level']}",
        f"Crop Loss\n{result['loss_pct']}%",
    ]]
    risk_table = Table(risk_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), LIGHT),
        ('BACKGROUND',   (1,0), (1,0),   colors.HexColor(
            "#fef2f2" if result['risk_level']=='HIGH' else
            "#fffbeb" if result['risk_level']=='MEDIUM' else
            "#f0fdf4"
        )),
        ('TEXTCOLOR',    (1,0), (1,0),   risk_color),
        ('FONTNAME',     (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 12),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT, LIGHT]),
        ('BOX',          (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID',    (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING',   (0,0), (-1,-1), 14),
        ('BOTTOMPADDING',(0,0), (-1,-1), 14),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Insurance Details ──
    story.append(Paragraph("INSURANCE DETAILS (PMFBY)", section_style))

    ins_data = [
        ["Field",                   "Value"],
        ["Sum Insured",             result['sum_insured']],
        ["Historical Avg Yield",    f"{result['hist_avg']} tons/hectare"],
        ["Current Yield",           f"{result['yield_val']} tons/hectare"],
        ["Trigger Level",           result['trigger']],
        ["Payout Percentage",       f"{result['payout_pct']}%"],
        ["Payout Amount",           result['payout_amount']],
        ["Insurance Decision",      "✅ ELIGIBLE" if result['eligible'] else "❌ NOT ELIGIBLE"],
    ]
    ins_table = Table(ins_data, colWidths=[8*cm, 8.5*cm])
    ins_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  DARK),
        ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1), (0,-1),  'Helvetica-Bold'),
        ('FONTNAME',      (1,1), (1,-1),  'Helvetica'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,1), (0,-1),  GREY),
        ('TEXTCOLOR',     (1,-1),(1,-1),  GREEN if result['eligible'] else RED),
        ('FONTNAME',      (1,-1),(1,-1),  'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, colors.HexColor("#f8fafc")]),
        ('BOX',           (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ]))
    story.append(ins_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Live Weather (if available) ──
    if weather and weather.get('found'):
        story.append(Paragraph("LIVE WEATHER CONDITIONS", section_style))
        weather_data = [
            ["Temperature", "Humidity", "Rainfall", "Condition"],
            [
                f"{weather['temperature']}°C",
                f"{weather['humidity']}%",
                f"{weather['rainfall']} mm",
                weather['condition'],
            ]
        ]
        w_table = Table(weather_data, colWidths=[4*cm, 4*cm, 4*cm, 4.5*cm])
        w_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor("#0ea5e9")),
            ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
            ('FONTNAME',      (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.HexColor("#f0f9ff")]),
            ('BOX',           (0,0), (-1,-1), 1, colors.HexColor("#bae6fd")),
            ('INNERGRID',     (0,0), (-1,-1), 0.5, colors.HexColor("#bae6fd")),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(w_table)
        story.append(Spacer(1, 0.3*cm))

    # ── Decision Box ──
    story.append(Spacer(1, 0.3*cm))
    decision_text = (
        f"✅ ELIGIBLE FOR PMFBY INSURANCE PAYOUT — {result['payout_amount']}"
        if result['eligible'] else
        f"❌ NOT ELIGIBLE — Crop loss ({result['loss_pct']}%) is below 25% threshold"
    )
    decision_style = ParagraphStyle(
        'Decision', fontSize=11, fontName='Helvetica-Bold',
        textColor=GREEN if result['eligible'] else RED,
        alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph(decision_text, decision_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3*cm))

    # ── Footer ──
    story.append(Paragraph(
        "This report was generated by AgriInsure AI System. "
        "For official claims, please visit your nearest agriculture office "
        "or the PMFBY portal at pmfby.gov.in",
        small_style
    ))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y')} | "
        "AI-Based Agricultural Risk & Insurance Trigger System",
        small_style
    ))

    doc.build(story)
    return output_path


# ── Test ──
if __name__ == "__main__":
    test_result = {
        'district': 'NAMAKKAL', 'crop': 'Groundnut',
        'area': 2.5, 'yield_val': 0.8, 'hist_avg': 1.5,
        'risk_score': 78.5, 'risk_level': 'HIGH',
        'sum_insured': '₹38,000', 'loss_pct': 46.7,
        'payout_pct': 50, 'payout_amount': '₹19,000',
        'trigger': 'Moderate Loss', 'eligible': True,
        'season': 'Kharif',
    }
    path = generate_risk_pdf(test_result)
    print(f"✅ PDF saved to: {path}")