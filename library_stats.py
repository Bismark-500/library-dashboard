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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
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

# ========== GENERATE PDF REPORT ==========
def generate_pdf_report(df, month_name, year):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
        pdf_path = tmpfile.name
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1,
        spaceAfter=30
    )
    story.append(Paragraph(f"Prempeh II Library", title_style))
    story.append(Paragraph(f"Monthly Report - {month_name} {year}", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Executive Summary", styles['Heading3']))
    story.append(Spacer(1, 10))
    
    df_month = df[df['month_year'] == f"{month_name} {year}"]
    total_visitors = df_month['count'].sum()
    days_active = df_month['date'].nunique()
    avg_daily = total_visitors / days_active if days_active > 0 else 0
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Visitors", f"{total_visitors:,}"],
        ["Days Active", str(days_active)],
        ["Average Daily", f"{avg_daily:.0f}"],
        ["Busiest Floor", df_month.groupby('floor')['count'].sum().idxmax()],
        ["Peak Time", df_month.groupby('time_slot')['count'].sum().idxmax()]
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Daily Totals", styles['Heading3']))
    story.append(Spacer(1, 10))
    
    daily_totals = df_month.groupby('date')['count'].sum().reset_index()
    daily_totals.columns = ['Date', 'Total Visitors']
    daily_totals['Date'] = pd.to_datetime(daily_totals['Date']).dt.strftime('%B %d')
    
    daily_table_data = [daily_totals.columns.tolist()] + daily_totals.values.tolist()
    daily_table = Table(daily_table_data, colWidths=[2*inch, 2*inch])
    daily_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (1, -1), 1, colors.black)
    ]))
    story.append(daily_table)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Floor Usage Summary", styles['Heading3']))
    story.append(Spacer(1, 10))
    
    floor_data = df_month.groupby('floor')['count'].sum().reset_index()
    floor_data.columns = ['Floor', 'Total Visitors']
    floor_data = floor_data.sort_values('Total Visitors', ascending=False)
    
    floor_table_data = [floor_data.columns.tolist()] + floor_data.values.tolist()
    floor_table = Table(floor_table_data, colWidths=[2.5*inch, 2.5*inch])
    floor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (1, -1), 1, colors.black)
    ]))
    story.append(floor_table)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Time Slot Usage", styles['Heading3']))
    story.append(Spacer(1, 10))
    
    time_data = df_month.groupby('time_slot')['count'].sum().reset_index()
    time_data.columns = ['Time Slot', 'Total Visitors']
    
    time_table_data = [time_data.columns.tolist()] + time_data.values.tolist()
    time_table = Table(time_table_data, colWidths=[2.5*inch, 2.5*inch])
    time_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (1, -1), 1, colors.black)
    ]))
    story.append(time_table)
    
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['Normal']))
    story.append(Paragraph("Data source: Prempeh II Library Daily Counts", styles['Normal']))
    
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
    for (time_slot, floor), val in entered_data.items():
        col_totals[floor] += val
    
    total_cols = st.columns([1.5] + [1.2] * len(floors) + [1])
    total_cols[0].write("**Total**")
    grand_total = 0
    for i, floor in enumerate(floors):
        total_cols[i+1].write(f"**{col_totals[floor]}**")
        grand_total += col_totals[floor]
    total_cols[-1].write(f"**{grand_total}**")
    
    if st.button("📋 STAGE CHANGES FOR THIS DAY", type="secondary", use_container_width=True):
        new_rows = []
        for time_slot in time_slots:
            for floor in floors:
                new_rows.append({
                    "date": date_str,
                    "day": selected_day,
                    "floor": floor,
                    "time_slot": time_slot,
                    "count": entered_data.get((time_slot, floor), 0)
                })
        
        new_df = pd.DataFrame(new_rows)
        
        if len(st.session_state.df_working) > 0:
            st.session_state.df_working = st.session_state.df_working[st.session_state.df_working["date"] != date_str]
            st.session_state.df_working = pd.concat([st.session_state.df_working, new_df], ignore_index=True)
        else:
            st.session_state.df_working = new_df
        
        st.session_state.has_unsaved_changes = True
        st.success(f"✅ {selected_day}, {date_str} STAGED! Click 'SAVE ALL CHANGES' in sidebar when done.")
        st.rerun()
    
    st.divider()
    st.subheader("📋 Days Staged (Unsaved)")
    
    if len(st.session_state.df_working) > 0:
        working_dates = sorted(st.session_state.df_working["date"].unique())
        st.write(f"**Total days staged:** {len(working_dates)}")
        for d in working_dates:
            day_total = st.session_state.df_working[st.session_state.df_working["date"] == d]['count'].sum()
            try:
                day_name = datetime.strptime(d, "%Y-%m-%d").strftime("%A")
                st.write(f"   - {day_name} ({d}): {day_total:,} visitors")
            except:
                st.write(f"   - {d}: {day_total:,} visitors")
    else:
        st.write("No days staged yet.")

# ========== PAGE 2: EXECUTIVE DASHBOARD ==========
elif page == "📊 Executive Dashboard":
    display_df = st.session_state.df_working
    
    if len(display_df) == 0:
        st.warning("No data yet. Add data in 'Add/Edit Days' page.")
        st.stop()
    
    temp_df = display_df.copy()
    temp_df['date_obj'] = pd.to_datetime(temp_df['date'])
    temp_df['month_year'] = temp_df['date_obj'].dt.strftime('%B %Y')
    temp_df['weekday'] = temp_df['date_obj'].dt.day_name()
    
    available_months_list = sorted(temp_df['month_year'].unique(), reverse=True)
    available_weekdays = [d for d in days_order if d in temp_df['weekday'].unique()]
    
    # palette used across every chart on this page (gives the "3D" glossy feel via shading + pull)
    palette = ['#2E86AB', '#48C9B0', '#F5B041', '#EB5757', '#5DADE2', '#A569BD', '#58D68D', '#F1948A']
    
    main_col, filter_col = st.columns([5, 1.15])
    
    # ---------- FILTER / SLICER PANEL (right side) ----------
    with filter_col:
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<div class='filter-title'>📅 Month</div>", unsafe_allow_html=True)
        selected_month = st.selectbox("Month", available_months_list, key="dashboard_month", label_visibility="collapsed")
        
        st.markdown("<div class='filter-title'>🏢 Floor</div>", unsafe_allow_html=True)
        floor_filter = st.multiselect("Floor", floors, default=floors, key="floor_filter", label_visibility="collapsed")
        
        st.markdown("<div class='filter-title'>⏰ Time Slot</div>", unsafe_allow_html=True)
        time_filter = st.multiselect("Time Slot", time_slots, default=time_slots, key="time_filter", label_visibility="collapsed")
        
        st.markdown("<div class='filter-title'>📆 Day</div>", unsafe_allow_html=True)
        day_filter = st.multiselect("Day", available_weekdays, default=available_weekdays, key="day_filter", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    df = temp_df[
        (temp_df['month_year'] == selected_month) &
        (temp_df['floor'].isin(floor_filter if floor_filter else floors)) &
        (temp_df['time_slot'].isin(time_filter if time_filter else time_slots)) &
        (temp_df['weekday'].isin(day_filter if day_filter else available_weekdays))
    ]
    
    with main_col:
        # ---------- BANNER ----------
        st.markdown("""
        <div class='dash-banner'>
            <div class='icon'>🏛️📚</div>
            <div>
                <h1>PREMPEH II LIBRARY DASHBOARD</h1>
                <p>Real-Time Visitor Analytics</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if len(df) == 0:
            st.warning(f"No data for the selected filters in {selected_month}")
            st.stop()
        
        # ---------- KPI METRICS ----------
        total_visitors = df['count'].sum()
        days_active = df['date'].nunique()
        avg_daily = total_visitors / days_active if days_active > 0 else 0
        
        daily_totals = df.groupby('date_obj')['count'].sum()
        busiest_day = daily_totals.idxmax().strftime('%a, %b %d') if len(daily_totals) > 0 else "N/A"
        
        busiest_floor = df.groupby('floor')['count'].sum().idxmax()
        busiest_time = df.groupby('time_slot')['count'].sum().idxmax()
        
        kpi_accents = ['#2E86AB', '#48C9B0', '#F5B041', '#EB5757', '#A569BD']
        k1, k2, k3, k4, k5 = st.columns(5)
        kpi_defs = [
            (k1, "Total Visitors", f"{total_visitors:,}"),
            (k2, "Days Active", f"{days_active}"),
            (k3, "Avg Daily", f"{avg_daily:.0f}"),
            (k4, "Busiest Floor", busiest_floor),
            (k5, "Peak Time", busiest_time),
        ]
        for i, (col, label, value) in enumerate(kpi_defs):
            with col:
                st.markdown(f"""
                <div class='kpi-card' style='border-top-color:{kpi_accents[i]};'>
                    <div class='kpi-label'>{label}</div>
                    <div class='kpi-value' style='font-size:{"20px" if len(str(value))>10 else "24px"}'>{value}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.write("")
        
        tab_overview, tab_deep = st.tabs(["📊 Overview", "🔥 Deep Dive"])
        
        with tab_overview:
            # ---------- CHART ROW 1 ----------
            r1c1, r1c2, r1c3 = st.columns([1.1, 1.1, 1])
        
            with r1c1:
                st.markdown("<div class='chart-panel'><h4>📊 Visitors by Floor</h4>", unsafe_allow_html=True)
                floor_total = df.groupby('floor')['count'].sum().reindex(floors).fillna(0)
                fig_floor = go.Figure(go.Bar(
                    x=floor_total.index, y=floor_total.values,
                    marker=dict(color=palette[:len(floor_total)], line=dict(color='rgba(0,0,0,0.25)', width=1)),
                    text=floor_total.values, textposition='outside'
                ))
                fig_floor.update_layout(
                    height=250, margin=dict(l=10, r=10, t=10, b=60),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(tickangle=-30, showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
                )
                st.plotly_chart(fig_floor, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            with r1c2:
                st.markdown("<div class='chart-panel'><h4>⏰ Visitors by Time Slot</h4>", unsafe_allow_html=True)
                time_total = df.groupby('time_slot')['count'].sum().reindex(time_slots).fillna(0).sort_values()
                fig_time = go.Figure(go.Bar(
                    x=time_total.values, y=time_total.index, orientation='h',
                    marker=dict(color=palette[:len(time_total)], line=dict(color='rgba(0,0,0,0.25)', width=1)),
                    text=time_total.values, textposition='outside'
                ))
                fig_time.update_layout(
                    height=250, margin=dict(l=10, r=20, t=10, b=10),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_time, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            with r1c3:
                st.markdown("<div class='chart-panel'><h4>🏢 Floor Distribution</h4>", unsafe_allow_html=True)
                fig_floor_pie = go.Figure(go.Pie(
                    labels=floor_total.index, values=floor_total.values, hole=0.35,
                    pull=[0.06 if v == floor_total.max() else 0 for v in floor_total.values],
                    marker=dict(colors=palette[:len(floor_total)], line=dict(color='white', width=2)),
                    textinfo='percent'
                ))
                fig_floor_pie.update_layout(
                    height=250, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', showlegend=True,
                    legend=dict(orientation='h', yanchor='bottom', y=-0.25, font=dict(size=9))
                )
                st.plotly_chart(fig_floor_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            # ---------- CHART ROW 2 ----------
            r2c1, r2c2, r2c3 = st.columns([1.3, 1, 1])
        
            with r2c1:
                st.markdown(f"<div class='chart-panel'><h4>📈 Daily Visitor Trend — {selected_month}</h4>", unsafe_allow_html=True)
                daily_trend = df.groupby('date_obj')['count'].sum().reset_index()
                fig_trend = px.line(daily_trend, x='date_obj', y='count', markers=True,
                                     color_discrete_sequence=['#2E86AB'])
                fig_trend.update_traces(line=dict(width=3), marker=dict(size=8, color='#EB5757'))
                fig_trend.add_hline(y=daily_trend['count'].mean(), line_dash="dash",
                                     annotation_text=f"Avg: {daily_trend['count'].mean():.0f}",
                                     line_color="#A569BD")
                fig_trend.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)', title=None)
                )
                st.plotly_chart(fig_trend, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            with r2c2:
                st.markdown("<div class='chart-panel'><h4>🌓 Early vs Late Week</h4>", unsafe_allow_html=True)
                early_days = ["Monday", "Tuesday", "Wednesday"]
                late_days = ["Thursday", "Friday"]
                early_total = df[df['weekday'].isin(early_days)]['count'].sum()
                late_total = df[df['weekday'].isin(late_days)]['count'].sum()
                fig_split = go.Figure(go.Pie(
                    labels=["Mon–Wed", "Thu–Fri"], values=[early_total, late_total], hole=0,
                    pull=[0.08, 0], marker=dict(colors=['#2E86AB', '#F5B041'], line=dict(color='white', width=2)),
                    textinfo='percent'
                ))
                fig_split.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', showlegend=True,
                    legend=dict(orientation='h', yanchor='bottom', y=-0.15, font=dict(size=9))
                )
                st.plotly_chart(fig_split, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            with r2c3:
                st.markdown("<div class='chart-panel'><h4>⏱️ Time Slot Share</h4>", unsafe_allow_html=True)
                time_total_ord = df.groupby('time_slot')['count'].sum().reindex(time_slots).fillna(0)
                fig_time_pie = go.Figure(go.Pie(
                    labels=time_total_ord.index, values=time_total_ord.values, hole=0,
                    pull=[0.1 if v == time_total_ord.max() else 0.02 for v in time_total_ord.values],
                    marker=dict(colors=palette[:len(time_total_ord)], line=dict(color='white', width=2)),
                    textinfo='percent'
                ))
                fig_time_pie.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', showlegend=True,
                    legend=dict(orientation='h', yanchor='bottom', y=-0.15, font=dict(size=9))
                )
                st.plotly_chart(fig_time_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with tab_deep:
            # ---------- ADVANCED ANALYTICS (heatmaps + weekly pattern) ----------
            r3c1, r3c2 = st.columns(2)
            with r3c1:
                st.markdown("<div class='chart-panel'><h4>🔥 Floor × Time Slot Heatmap</h4>", unsafe_allow_html=True)
                pivot = df.groupby(['floor', 'time_slot'])['count'].sum().unstack().reindex(columns=time_slots)
                fig_heat1 = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                                       labels={'x': 'Time Slot', 'y': 'Floor', 'color': 'Visitors'})
                fig_heat1.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_heat1, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            with r3c2:
                st.markdown("<div class='chart-panel'><h4>🔥 Day × Time Slot Heatmap</h4>", unsafe_allow_html=True)
                day_pivot = df.groupby(['weekday', 'time_slot'])['count'].sum().unstack().reindex(columns=time_slots)
                day_pivot = day_pivot.reindex([d for d in days_order if d in day_pivot.index])
                fig_heat2 = px.imshow(day_pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                                       labels={'x': 'Time Slot', 'y': 'Day', 'color': 'Visitors'})
                fig_heat2.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_heat2, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
            st.markdown("<div class='chart-panel'><h4>📅 Weekly Pattern</h4>", unsafe_allow_html=True)
            weekly_pattern = df.groupby('weekday')['count'].sum().reindex(days_order).dropna()
            fig_week = go.Figure(go.Bar(
                x=weekly_pattern.index, y=weekly_pattern.values,
                marker=dict(color=palette[:len(weekly_pattern)], line=dict(color='rgba(0,0,0,0.25)', width=1)),
                text=weekly_pattern.values, textposition='outside'
            ))
            fig_week.update_layout(
                height=250, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
            )
            st.plotly_chart(fig_week, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
            # ---------- KEY INSIGHTS ----------
            quietest_floor = df.groupby('floor')['count'].sum().idxmin()
            floor_ratio = (df.groupby('floor')['count'].sum()[busiest_floor] / df['count'].sum() * 100).round(1)
        
            st.markdown("<div class='insight-panel'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#123456;margin-top:0;'>💡 Key Insights & Recommendations</h4>", unsafe_allow_html=True)
            st.markdown(f"- 📌 **Peak Day:** {busiest_day} was the busiest day")
            st.markdown(f"- 📌 **Peak Time:** {busiest_time} is when most people visit")
            st.markdown(f"- 📌 **Floor Usage:** {busiest_floor} handles {floor_ratio}% of all traffic")
            st.markdown(f"- 📌 **Average Daily:** {avg_daily:.0f} visitors per day")
            if busiest_time in ["4pm", "8pm"]:
                st.markdown("- 💡 Consider adding more staff during peak hours")
            if floor_ratio > 40:
                st.markdown(f"- 💡 {busiest_floor} may need more seating or space")
            if days_active < 5:
                st.markdown("- 💡 Consider collecting data for more days to identify patterns")
            st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.has_unsaved_changes:
            st.warning("⚠️ You have unsaved changes. The dashboard shows UNSAVED data. Click 'SAVE ALL CHANGES' in sidebar to save to CSV.")

# ========== PAGE 3: DAILY VIEW ==========
elif page == "📅 Daily View":
    st.title("📅 Daily Detail View")
    
    display_df = st.session_state.df_working
    
    if len(display_df) == 0:
        st.warning("No data yet.")
        st.stop()
    
    temp_df = display_df.copy()
    temp_df['date_obj'] = pd.to_datetime(temp_df['date'])
    all_dates = sorted(temp_df['date_obj'].unique(), reverse=True)
    
    selected_date = st.selectbox("Select a date to view details", all_dates, format_func=lambda x: x.strftime("%A, %B %d, %Y"))
    
    date_data = temp_df[temp_df['date_obj'] == selected_date]
    
    if len(date_data) > 0:
        st.write(f"### Detailed Breakdown for {selected_date.strftime('%A, %B %d, %Y')}")
        daily_total = date_data['count'].sum()
        st.metric("Total Visitors This Day", f"{daily_total:,}")
        
        pivot_table = date_data.pivot_table(index="time_slot", columns="floor", values="count", fill_value=0)
        pivot_table["Total"] = pivot_table.sum(axis=1)
        st.dataframe(pivot_table, use_container_width=True)
    
    if st.session_state.has_unsaved_changes:
        st.info("⚠️ You have unsaved changes. These are shown above. Click 'SAVE ALL CHANGES' in sidebar to save.")

# ========== PAGE 4: MONTHLY REPORT & COMPARE ==========
else:
    st.title("📄 Monthly Report & Month-over-Month Comparison")
    
    display_df = st.session_state.df_working
    
    if len(display_df) == 0:
        st.warning("No data yet. Add data first.")
        st.stop()
    
    temp_df = display_df.copy()
    temp_df['date_obj'] = pd.to_datetime(temp_df['date'])
    temp_df['month_year'] = temp_df['date_obj'].dt.strftime('%B %Y')
    temp_df['month_num'] = temp_df['date_obj'].dt.month
    temp_df['year'] = temp_df['date_obj'].dt.year
    
    available_months = sorted(temp_df['month_year'].unique(), reverse=True)
    
    # ========== PDF REPORT SECTION ==========
    st.subheader("📑 Generate PDF Report")
    
    col1, col2 = st.columns(2)
    with col1:
        report_month = st.selectbox("Select month for PDF report", available_months, key="pdf_month")
    with col2:
        st.write("")  # spacer
    
    if st.button("📄 Generate PDF Report", type="primary"):
        report_month_name = report_month.split()[0]
        report_year = report_month.split()[1]
        pdf_path = generate_pdf_report(temp_df, report_month_name, int(report_year))
        
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_data,
            file_name=f"prempeh_library_{report_month_name}_{report_year}.pdf",
            mime="application/pdf"
        )
        st.success(f"✅ PDF report for {report_month} generated!")
        
        # Clean up temp file
        os.unlink(pdf_path)
    
    st.divider()
    
    # ========== MONTH-OVER-MONTH COMPARISON ==========
    st.subheader("📊 Month-over-Month Comparison")
    
    if len(available_months) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            month1 = st.selectbox("First Month", available_months, key="compare1")
        with col2:
            month2 = st.selectbox("Second Month", available_months, key="compare2")
        
        if month1 != month2:
            # Get data for both months
            df1 = temp_df[temp_df['month_year'] == month1]
            df2 = temp_df[temp_df['month_year'] == month2]
            
            # Calculate metrics
            total1 = df1['count'].sum()
            total2 = df2['count'].sum()
            days1 = df1['date'].nunique()
            days2 = df2['date'].nunique()
            avg1 = total1 / days1 if days1 > 0 else 0
            avg2 = total2 / days2 if days2 > 0 else 0
            
            # Calculate changes
            total_change = ((total2 - total1) / total1 * 100) if total1 > 0 else 0
            avg_change = ((avg2 - avg1) / avg1 * 100) if avg1 > 0 else 0
            
            # Display comparison table
            st.write(f"### {month1} vs {month2}")
            
            comparison_data = {
                "Metric": ["Total Visitors", "Days Active", "Average Daily", "Busiest Day", "Peak Floor", "Peak Time"],
                month1: [
                    f"{total1:,}",
                    str(days1),
                    f"{avg1:.0f}",
                    df1.groupby('date_obj')['count'].sum().idxmax().strftime('%b %d') if len(df1) > 0 else "N/A",
                    df1.groupby('floor')['count'].sum().idxmax() if len(df1) > 0 else "N/A",
                    df1.groupby('time_slot')['count'].sum().idxmax() if len(df1) > 0 else "N/A"
                ],
                month2: [
                    f"{total2:,}",
                    str(days2),
                    f"{avg2:.0f}",
                    df2.groupby('date_obj')['count'].sum().idxmax().strftime('%b %d') if len(df2) > 0 else "N/A",
                    df2.groupby('floor')['count'].sum().idxmax() if len(df2) > 0 else "N/A",
                    df2.groupby('time_slot')['count'].sum().idxmax() if len(df2) > 0 else "N/A"
                ],
                "Change": [
                    f"{total_change:+.1f}%",
                    f"{days2 - days1:+.0f} days",
                    f"{avg_change:+.1f}%",
                    "",
                    "",
                    ""
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            # Visual comparison charts
            st.write("### Visual Comparison")
            
            # Bar chart comparing total visitors
            fig_compare = go.Figure(data=[
                go.Bar(name=month1, x=['Total Visitors'], y=[total1]),
                go.Bar(name=month2, x=['Total Visitors'], y=[total2])
            ])
            fig_compare.update_layout(title="Total Visitors Comparison", barmode='group')
            st.plotly_chart(fig_compare, use_container_width=True)
            
            # Floor comparison
            floor1 = df1.groupby('floor')['count'].sum().reset_index()
            floor1.columns = ['Floor', month1]
            floor2 = df2.groupby('floor')['count'].sum().reset_index()
            floor2.columns = ['Floor', month2]
            floor_compare = pd.merge(floor1, floor2, on='Floor', how='outer').fillna(0)
            
            fig_floor = go.Figure(data=[
                go.Bar(name=month1, x=floor_compare['Floor'], y=floor_compare[month1]),
                go.Bar(name=month2, x=floor_compare['Floor'], y=floor_compare[month2])
            ])
            fig_floor.update_layout(title="Floor Usage Comparison", barmode='group', xaxis_tickangle=-45)
            st.plotly_chart(fig_floor, use_container_width=True)
            
            # Insight
            st.divider()
            if total_change > 5:
                st.success(f"📈 **Positive Growth:** {month2} had {total_change:.1f}% more visitors than {month1}")
            elif total_change < -5:
                st.warning(f"📉 **Decline:** {month2} had {abs(total_change):.1f}% fewer visitors than {month1}")
            else:
                st.info(f"📊 **Stable:** Visitor numbers remained relatively stable between {month1} and {month2}")
        else:
            st.warning("Please select two different months to compare")
    else:
        st.info("Need at least two months of data to show month-over-month comparison. Keep adding data!")
