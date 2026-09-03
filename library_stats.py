import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import requests
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import tempfile
import base64

st.set_page_config(page_title="Prempeh II Library", layout="wide")

# ========== GLOBAL THEME / CSS ==========
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #eaf5fb 0%, #dbeef9 100%); }
.block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.4rem; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { background: #ffffff; border-radius: 8px 8px 0 0; padding: 6px 16px; font-weight: 700; color: #123456; }
.dash-banner {
    background: linear-gradient(90deg, #eaf6fb 0%, #cfe9f7 100%);
    border: 2px solid #123456; border-radius: 10px;
    padding: 14px 24px; margin-bottom: 18px;
    display: flex; align-items: center; gap: 14px;
}
.dash-banner .icon { font-size: 34px; }
.dash-banner h1 {
    font-family: Georgia, 'Times New Roman', serif;
    color: #123456; font-size: 32px; margin: 0; letter-spacing: 1px;
}
.dash-banner p { margin: 0; color: #35597a; font-size: 13px; font-weight: 600; }
.kpi-card {
    background: #ffffff; border-radius: 12px; padding: 14px 8px 10px 8px;
    text-align: center; box-shadow: 0 4px 10px rgba(20,60,90,0.15);
    border-top: 5px solid #2E86AB; height: 100%;
}
.kpi-label {
    font-size: 11px; font-weight: 800; color: #5a7d97;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;
}
.kpi-value { font-size: 24px; font-weight: 800; color: #123456; }
.chart-panel {
    background: #ffffff; border-radius: 12px; padding: 10px 16px 2px 16px;
    box-shadow: 0 4px 10px rgba(20,60,90,0.12); margin-bottom: 16px;
}
.chart-panel h4 {
    color: #123456; font-size: 14px; font-weight: 800; margin: 4px 0 0 0;
    border-bottom: 2px solid #d6ecf8; padding-bottom: 6px;
}
.filter-panel {
    background: #ffffff; border-radius: 12px; padding: 14px 14px 4px 14px;
    box-shadow: 0 4px 10px rgba(20,60,90,0.12); height: 100%;
}
.filter-title {
    font-size: 12px; font-weight: 800; color: #123456; margin: 12px 0 2px 0;
    border-bottom: 2px solid #123456; padding-bottom: 4px; text-transform: uppercase;
}
.insight-panel {
    background: #ffffff; border-radius: 12px; padding: 14px 18px;
    box-shadow: 0 4px 10px rgba(20,60,90,0.12); margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ========== YOUR GOOGLE SHEET ID ==========
SHEET_ID = "1NG8yGF392pDoKE7JRunwbfRU1PAAcnoBH6rnSmXs-wo"

# ========== DEFINE ALL CONSTANTS ==========
floors = ["Ground floor", "First floor", "Second floor", "Third floor", "Fourth floor", "Research Commons"]
time_slots = ["11am", "2pm", "4pm", "8pm"]
days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DASHBOARD_URL = "https://prempeh-libraryuser.streamlit.app/"

# Local CSV file
LOCAL_DATA_FILE = os.path.join(os.path.dirname(__file__), "prempeh_library_all_data.csv")

# ========== TIME FORMAT CONVERTER ==========
def convert_time_format(time_str):
    if pd.isna(time_str):
        return time_str
    time_str = str(time_str)
    time_map = {
        "11:00": "11am", "14:00": "2pm", "16:00": "4pm", "20:00": "8pm",
        "11:0": "11am", "14:0": "2pm", "16:0": "4pm", "20:0": "8pm",
        "11": "11am", "14": "2pm", "16": "4pm", "20": "8pm"
    }
    return time_map.get(time_str, time_str)

# ========== DATE FORMAT CONVERTER ==========
def convert_date_format(date_str):
    if pd.isna(date_str):
        return date_str
    date_str = str(date_str)
    if date_str.count('-') == 2 and len(date_str.split('-')[0]) == 4:
        return date_str
    try:
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts[0]) <= 2:
                return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        pass
    try:
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except:
        return date_str

# ========== CLEAN DATA ==========
def clean_data(df):
    if len(df) == 0:
        return df
    df = df.copy()
    if 'time_slot' in df.columns:
        df['time_slot'] = df['time_slot'].apply(convert_time_format)
    if 'date' in df.columns:
        df['date'] = df['date'].apply(convert_date_format)
    return df

# ========== LOAD FROM GOOGLE SHEET ==========
def load_from_google_sheet():
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        response = requests.get(csv_url)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            if len(df) > 0 and 'date' in df.columns:
                df = clean_data(df)
                return df
    except Exception as e:
        pass
    return pd.DataFrame(columns=["date", "day", "floor", "time_slot", "count"])

# ========== LOAD ALL DATA ==========
def load_all_data():
    df = load_from_google_sheet()
    if len(df) > 0:
        return df
    if os.path.exists(LOCAL_DATA_FILE):
        df = pd.read_csv(LOCAL_DATA_FILE)
        required = ["date", "day", "floor", "time_slot", "count"]
        existing_cols = [c for c in required if c in df.columns]
        df = df[existing_cols]
        df = clean_data(df)
        return df
    return pd.DataFrame(columns=["date", "day", "floor", "time_slot", "count"])

# ========== SAVE ALL DATA ==========
def save_all_data(df):
    try:
        required_columns = ["date", "day", "floor", "time_slot", "count"]
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        cols_to_save = [c for c in required_columns if c in df.columns]
        df_to_save = df[cols_to_save].copy()
        df_to_save = clean_data(df_to_save)
        df_to_save.to_csv(LOCAL_DATA_FILE, index=False)
        return os.path.exists(LOCAL_DATA_FILE)
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

# ========== PDF HELPERS ==========
NAVY = colors.HexColor('#123456')
BLUE = colors.HexColor('#2E86AB')
TEAL = colors.HexColor('#48C9B0')
AMBER = colors.HexColor('#F5B041')
CORAL = colors.HexColor('#EB5757')
LIGHT_BG = colors.HexColor('#EAF5FB')
ROW_ALT = colors.HexColor('#F4FAFD')

def _styled_table(data, col_widths, header_color=BLUE, align='CENTER'):
    """A clean table with a colored header row and soft alternating row shading."""
    table = Table(data, colWidths=col_widths, hAlign='CENTER')
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9.5),
        ('ALIGN', (0, 0), (-1, -1), align),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, 0), 1, header_color),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#DCE9F2')),
        ('TEXTCOLOR', (0, 1), (-1, -1), NAVY),
    ]
    for r in range(1, len(data)):
        if r % 2 == 0:
            style.append(('BACKGROUND', (0, r), (-1, r), ROW_ALT))
    table.setStyle(TableStyle(style))
    return table

def _bar_chart_drawing(categories, values, bar_color, width=520, height=170, value_fmt="{:.0f}"):
    """A dependency-free bar chart (reportlab.graphics) for embedding in the PDF."""
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart

    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 40
    chart.width = width - 70
    chart.height = height - 70
    chart.data = [values]
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.angle = 20
    chart.categoryAxis.labels.dx = -6
    chart.categoryAxis.labels.dy = -10
    chart.categoryAxis.labels.fontSize = 7.5
    chart.categoryAxis.labels.fillColor = NAVY
    chart.valueAxis.valueMin = 0
    top = max(values) if values else 1
    chart.valueAxis.valueMax = top * 1.2 if top > 0 else 1
    chart.valueAxis.labels.fontSize = 7.5
    chart.valueAxis.labels.fillColor = NAVY
    chart.bars[0].fillColor = bar_color
    chart.bars[0].strokeColor = None
    chart.barLabels.fontSize = 7.5
    chart.barLabels.fillColor = NAVY
    chart.barLabelFormat = value_fmt
    chart.barLabels.dy = 4
    drawing.add(chart)
    return drawing

# ========== GENERATE PDF REPORT ==========
def generate_pdf_report(df, month_name, year):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
        pdf_path = tmpfile.name
    
    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        topMargin=0.5*inch, bottomMargin=0.5*inch,
        leftMargin=0.6*inch, rightMargin=0.6*inch
    )
    styles = getSampleStyleSheet()
    story = []
    
    df_month = df[df['month_year'] == f"{month_name} {year}"].copy()
    total_visitors = df_month['count'].sum()
    days_active = df_month['date'].nunique()
    avg_daily = total_visitors / days_active if days_active > 0 else 0
    
    floor_totals = df_month.groupby('floor')['count'].sum().reindex(floors).fillna(0)
    time_totals = df_month.groupby('time_slot')['count'].sum().reindex(time_slots).fillna(0)
    daily_totals_df = df_month.groupby('date')['count'].sum().reset_index()
    daily_totals_df.columns = ['Date', 'Total Visitors']
    daily_totals_df['DateObj'] = pd.to_datetime(daily_totals_df['Date'])
    daily_totals_df = daily_totals_df.sort_values('DateObj')
    
    busiest_floor = floor_totals.idxmax()
    quietest_floor = floor_totals.idxmin()
    busiest_time = time_totals.idxmax()
    busiest_day_row = daily_totals_df.loc[daily_totals_df['Total Visitors'].idxmax()] if len(daily_totals_df) > 0 else None
    floor_share = (floor_totals[busiest_floor] / total_visitors * 100) if total_visitors > 0 else 0
    
    # ---------- HEADER BANNER ----------
    header_style = ParagraphStyle('HeaderTitle', parent=styles['Normal'], fontSize=20,
                                   textColor=colors.whitesmoke, fontName='Helvetica-Bold', leading=24)
    subheader_style = ParagraphStyle('HeaderSub', parent=styles['Normal'], fontSize=11,
                                      textColor=colors.HexColor('#D6ECF8'), fontName='Helvetica', leading=14)
    banner_content = [
        [Paragraph("🏛️ Prempeh II Library", header_style)],
        [Paragraph(f"Monthly Usage Report — {month_name} {year}", subheader_style)]
    ]
    banner = Table(banner_content, colWidths=[6.8*inch])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TOPPADDING', (0, 0), (-1, 0), 16),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 16),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 18),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(banner)
    story.append(Spacer(1, 18))
    
    # ---------- NARRATIVE PREAMBLE ----------
    intro_style = ParagraphStyle('Intro', parent=styles['Normal'], fontSize=10.3,
                                  textColor=NAVY, leading=15)
    preamble = (
        f"This report presents a summary of library usage at Prempeh II Library for the month of "
        f"<b>{month_name} {year}</b>. Over <b>{days_active} recorded day{'s' if days_active != 1 else ''}</b>, "
        f"the library welcomed a total of <b>{total_visitors:,} visitors</b>, averaging "
        f"<b>{avg_daily:.0f} visitors per day</b>. The sections below break usage down by floor, time slot, "
        f"and day, to help guide staffing, space planning, and resource allocation for the month ahead."
    )
    story.append(Paragraph(preamble, intro_style))
    story.append(Spacer(1, 16))
    
    # ---------- EXECUTIVE SUMMARY ----------
    story.append(Paragraph("Executive Summary", ParagraphStyle('H3', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 6))
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Visitors", f"{total_visitors:,}"],
        ["Days Active", str(days_active)],
        ["Average Daily", f"{avg_daily:.0f}"],
        ["Busiest Floor", busiest_floor],
        ["Peak Time", busiest_time],
    ]
    if busiest_day_row is not None:
        summary_data.append(["Busiest Day", busiest_day_row['DateObj'].strftime('%A, %B %d')])
    
    story.append(_styled_table(summary_data, [3*inch, 3.2*inch], header_color=BLUE, align='LEFT'))
    story.append(Spacer(1, 20))
    
    # ---------- DAILY TREND LINE CHART (NEW) ----------
    story.append(Paragraph("Daily Traffic Trend", ParagraphStyle('H3g', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 4))
    
    trend_note_style = ParagraphStyle('TrendNote', parent=styles['Normal'], fontSize=9,
                                       textColor=colors.HexColor('#5a7d97'), leading=13)
    story.append(Paragraph(
        "The line chart below shows the total number of visitors recorded each day throughout the month. "
        "The dashed horizontal line represents the average daily traffic for the period.",
        trend_note_style
    ))
    story.append(Spacer(1, 8))
    
    # Build the daily trend chart using reportlab graphics
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    
    trend_dates = daily_totals_df['DateObj'].dt.strftime('%d %b').tolist()
    trend_values = daily_totals_df['Total Visitors'].tolist()
    
    # Create the line chart
    trend_chart = Drawing(550, 200)
    line_chart = HorizontalLineChart()
    line_chart.x = 50
    line_chart.y = 30
    line_chart.width = 460
    line_chart.height = 140
    line_chart.data = [trend_values]
    line_chart.categoryAxis.categoryNames = trend_dates
    line_chart.categoryAxis.labels.angle = 45
    line_chart.categoryAxis.labels.dx = -8
    line_chart.categoryAxis.labels.dy = -12
    line_chart.categoryAxis.labels.fontSize = 7
    line_chart.categoryAxis.labels.fillColor = NAVY
    line_chart.valueAxis.valueMin = 0
    top = max(trend_values) if trend_values else 1
    line_chart.valueAxis.valueMax = top * 1.15 if top > 0 else 1
    line_chart.valueAxis.labels.fontSize = 7
    line_chart.valueAxis.labels.fillColor = NAVY
    line_chart.lines[0].strokeColor = BLUE
    line_chart.lines[0].strokeWidth = 2.5
    line_chart.lines[0].symbol = 'circle'
    line_chart.lines[0].symbolSize = 5
    line_chart.lines[0].symbolFillColor = colors.HexColor('#EB5757')
    # Add average line as a horizontal line
    avg_line_value = avg_daily
    if avg_line_value > 0:
        # Add a custom horizontal line annotation using a drawing
        avg_line_y = 30 + (avg_line_value / line_chart.valueAxis.valueMax) * 140
        line_chart.valueAxis.rangeRound = 'both'
    trend_chart.add(line_chart)
    
    # Add average annotation below the chart
    story.append(trend_chart)
    story.append(Spacer(1, 4))
    avg_style = ParagraphStyle('AvgNote', parent=styles['Normal'], fontSize=8,
                                textColor=colors.HexColor('#EB5757'), alignment=TA_CENTER)
    story.append(Paragraph(f"Average daily visitors: {avg_daily:.0f} (dashed line)", avg_style))
    story.append(Spacer(1, 20))
    
    # ---------- VISUAL SNAPSHOT ----------
    story.append(Paragraph("Visual Snapshot", ParagraphStyle('H3b', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 6))
    
    floor_labels_short = [f.replace(" floor", "").replace("Research Commons", "Research") for f in floor_totals.index]
    floor_chart = _bar_chart_drawing(floor_labels_short, list(floor_totals.values), BLUE, width=250, height=175)
    time_chart = _bar_chart_drawing(list(time_totals.index), list(time_totals.values), AMBER, width=250, height=175)
    
    chart_caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9,
                                          textColor=colors.HexColor('#5a7d97'), alignment=TA_CENTER)
    charts_table = Table(
        [[floor_chart, time_chart],
         [Paragraph("Visitors by Floor", chart_caption_style), Paragraph("Visitors by Time Slot", chart_caption_style)]],
        colWidths=[3.3*inch, 3.3*inch]
    )
    charts_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
    ]))
    story.append(charts_table)
    story.append(Spacer(1, 20))
    
    # ---------- FLOOR USAGE ----------
    story.append(Paragraph("Floor Usage Summary", ParagraphStyle('H3d', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 6))
    
    floor_sorted = floor_totals.sort_values(ascending=False).reset_index()
    floor_sorted.columns = ['Floor', 'Total Visitors']
    floor_table_data = [["Floor", "Total Visitors"]] + floor_sorted.values.tolist()
    story.append(_styled_table(floor_table_data, [3.5*inch, 2.7*inch], header_color=colors.HexColor('#58D68D')))
    story.append(Spacer(1, 20))
    
    # ---------- TIME SLOT USAGE ----------
    story.append(Paragraph("Time Slot Usage", ParagraphStyle('H3e', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 6))
    
    time_table_data = [["Time Slot", "Total Visitors"]] + [[k, v] for k, v in time_totals.items()]
    story.append(_styled_table(time_table_data, [3.5*inch, 2.7*inch], header_color=CORAL))
    story.append(Spacer(1, 20))
    
    # ---------- DAILY TOTALS (detailed day-by-day appendix) ----------
    story.append(Paragraph("Daily Totals", ParagraphStyle('H3c', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 6))
    
    daily_note_style = ParagraphStyle('DailyNote', parent=styles['Normal'], fontSize=9,
                                       textColor=colors.HexColor('#5a7d97'), leading=13)
    story.append(Paragraph("A day-by-day breakdown of total visitors for the month, for reference.", daily_note_style))
    story.append(Spacer(1, 8))
    
    daily_display = daily_totals_df.copy()
    daily_display['Date'] = daily_display['DateObj'].dt.strftime('%B %d (%a)')
    daily_table_data = [["Date", "Total Visitors"]] + daily_display[['Date', 'Total Visitors']].values.tolist()
    story.append(_styled_table(daily_table_data, [3.5*inch, 2.7*inch], header_color=TEAL))
    story.append(Spacer(1, 20))
    
    # ---------- KEY INSIGHTS ----------
    story.append(Paragraph("Key Insights", ParagraphStyle('H3f', parent=styles['Heading3'], textColor=NAVY)))
    story.append(Spacer(1, 6))
    
    insight_style = ParagraphStyle('Insight', parent=styles['Normal'], fontSize=9.7, textColor=NAVY, leading=15)
    insights = [
        f"<b>{busiest_floor}</b> was the most used floor, accounting for {floor_share:.1f}% of all recorded traffic.",
        f"<b>{busiest_time}</b> was the peak time slot across the month.",
        f"<b>{quietest_floor}</b> saw the lightest traffic and may have room for repurposing or promotion.",
    ]
    if busiest_day_row is not None:
        insights.insert(0, f"The busiest single day was <b>{busiest_day_row['DateObj'].strftime('%A, %B %d')}</b> with {int(busiest_day_row['Total Visitors']):,} visitors.")
    
    insight_table_rows = [[Paragraph(f"•  {t}", insight_style)] for t in insights]
    insight_box = Table(insight_table_rows, colWidths=[6.8*inch])
    insight_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CFE9F7')),
    ]))
    story.append(insight_box)
    story.append(Spacer(1, 26))
    
    # ---------- FOOTER: LIVE DASHBOARD LINK ----------
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CFE9F7')))
    story.append(Spacer(1, 12))
    
    link_style = ParagraphStyle('Link', parent=styles['Normal'], fontSize=11,
                                 textColor=colors.whitesmoke, fontName='Helvetica-Bold', alignment=TA_CENTER)
    link_para = Paragraph(f'<a href="{DASHBOARD_URL}" color="white">📊 Click here to view the live dashboard</a>', link_style)
    link_button = Table([[link_para]], colWidths=[4*inch])
    link_button.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    footer_wrap = Table([[link_button]], colWidths=[6.8*inch])
    footer_wrap.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(footer_wrap)
    story.append(Spacer(1, 6))
    
    link_note_style = ParagraphStyle('LinkNote', parent=styles['Normal'], fontSize=8,
                                      textColor=colors.HexColor('#5a7d97'), alignment=TA_CENTER,
                                      fontName='Helvetica-Oblique')
    story.append(Paragraph("Best viewed on a computer — the dashboard isn't optimized for phones yet.", link_note_style))
    story.append(Spacer(1, 10))
    
    footer_text_style = ParagraphStyle('FooterText', parent=styles['Normal'], fontSize=8.3,
                                        textColor=colors.HexColor('#5a7d97'), alignment=TA_CENTER)
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", footer_text_style))
    story.append(Paragraph("Data source: Prempeh II Library Daily Counts", footer_text_style))
    
    doc.build(story)
    return pdf_path

# Initialize session state
if 'df_saved' not in st.session_state:
    st.session_state.df_saved = load_all_data()
if 'df_working' not in st.session_state:
    st.session_state.df_working = st.session_state.df_saved.copy()
if 'has_unsaved_changes' not in st.session_state:
    st.session_state.has_unsaved_changes = False

# ========== SIDEBAR ==========
st.sidebar.title("🏛️ Prempeh II Library")
st.sidebar.caption("Batch Entry - Save All at Once")

if len(st.session_state.df_saved) > 0:
    total_visitors = st.session_state.df_saved['count'].sum()
    total_days = st.session_state.df_saved['date'].nunique()
    st.sidebar.success(f"✅ Saved: {total_days} days • {total_visitors:,} visitors")
else:
    st.sidebar.info("📝 No saved data yet")

if st.session_state.has_unsaved_changes:
    st.sidebar.warning("⚠️ You have UNSAVED changes!")

st.sidebar.divider()

if st.sidebar.button("💾 SAVE ALL CHANGES", type="primary", use_container_width=True):
    if save_all_data(st.session_state.df_working):
        st.session_state.df_saved = st.session_state.df_working.copy()
        st.session_state.has_unsaved_changes = False
        st.sidebar.success("✅ All changes saved to CSV!")
        st.balloons()
        st.rerun()
    else:
        st.sidebar.error("❌ Save failed")

if len(st.session_state.df_working) > 0:
    csv_data = st.session_state.df_working.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Download CSV (All Days)",
        data=csv_data,
        file_name="prempeh_library_all_data.csv",
        mime="text/csv",
        use_container_width=True
    )

if len(st.session_state.df_working) > 0:
    csv_data = st.session_state.df_working.to_csv(index=False)
    st.sidebar.download_button(
        label="☁️ CSV for Google Sheet",
        data=csv_data,
        file_name="prempeh_library_all_data.csv",
        mime="text/csv",
        use_container_width=True
    )

if st.session_state.has_unsaved_changes:
    st.sidebar.divider()
    if st.sidebar.button("🗑️ DISCARD ALL UNSAVED", use_container_width=True):
        st.session_state.df_working = st.session_state.df_saved.copy()
        st.session_state.has_unsaved_changes = False
        st.success("✅ Unsaved changes discarded!")
        st.rerun()

page = st.sidebar.radio("Navigate:", ["📝 Add/Edit Days", "📊 Executive Dashboard", "📅 Daily View", "📄 Monthly Report & Compare"])

# ========== PAGE 1: ADD/EDIT DAYS ==========
if page == "📝 Add/Edit Days":
    st.title("🏛️ Prempeh II Library - Batch Data Entry")
    st.caption("Add new days or edit existing days. Click 'STAGE CHANGES' for each day. Then click 'SAVE ALL CHANGES' in sidebar when done.")
    
    if st.session_state.has_unsaved_changes:
        st.info("📝 You have unsaved changes. Click 'SAVE ALL CHANGES' in sidebar when finished with all days.")
    
    col1, col2 = st.columns(2)
    with col1:
        actual_date = st.date_input("Select Date", datetime.now())
    with col2:
        selected_day = actual_date.strftime("%A")
        st.write(f"**Day:** {selected_day}")
    
    date_str = actual_date.strftime("%Y-%m-%d")
    
    existing_data = st.session_state.df_working[st.session_state.df_working["date"] == date_str] if len(st.session_state.df_working) > 0 else pd.DataFrame()
    
    if len(existing_data) > 0:
        st.info(f"📌 Data EXISTS for {selected_day}. Edit below.")
    else:
        st.info(f"✨ No data yet for {selected_day}. Enter new data below.")
    
    st.write(f"### 📅 {selected_day}, {actual_date.strftime('%B %d, %Y')}")
    
    lookup = {}
    if len(existing_data) > 0:
        for _, row in existing_data.iterrows():
            lookup[(row['time_slot'], row['floor'])] = row['count']
    
    entered_data = {}
    
    header_cols = st.columns([1.5] + [1.2] * len(floors) + [1])
    header_cols[0].write("**Time → / Floor ↓**")
    for i, floor in enumerate(floors):
        header_cols[i+1].write(f"**{floor[:12]}**")
    header_cols[-1].write("**Total**")
    
    for time_slot in time_slots:
        row_cols = st.columns([1.5] + [1.2] * len(floors) + [1])
        row_cols[0].write(f"**{time_slot}**")
        
        row_total = 0
        for i, floor in enumerate(floors):
            existing_val = lookup.get((time_slot, floor), 0)
            key = f"batch_{date_str}_{time_slot}_{floor}"
            val = row_cols[i+1].text_input(
                "",
                value=str(existing_val) if existing_val != 0 else "",
                key=key,
                placeholder="0",
                label_visibility="collapsed"
            )
            try:
                count_val = int(val) if val.strip() else 0
            except:
                count_val = 0
            entered_data[(time_slot, floor)] = count_val
            row_total += count_val
        
        row_cols[-1].write(f"**{row_total}**")
    
    st.markdown("---")
    
    col_totals = {floor: 0 for floor in floors}
    for (time_slot, floor), val in entered
