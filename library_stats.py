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
    
    # Title
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
    
    # Summary section
    story.append(Paragraph("Executive Summary", styles['Heading3']))
    story.append(Spacer(1, 10))
    
    # Get monthly summary
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
    
    # Daily totals table
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
    
    # Floor distribution
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
    
    # Time slot distribution
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
    
    # Footer
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

# Show status
if len(st.session_state.df_saved) > 0:
    total_visitors = st.session_state.df_saved['count'].sum()
    total_days = st.session_state.df_saved['date'].nunique()
    st.sidebar.success(f"✅ Saved: {total_days} days • {total_visitors:,} visitors")
else:
    st.sidebar.info("📝 No saved data yet")

if st.session_state.has_unsaved_changes:
    st.sidebar.warning("⚠️ You have UNSAVED changes!")

st.sidebar.divider()

# SAVE ALL button
if st.sidebar.button("💾 SAVE ALL CHANGES", type="primary", use_container_width=True):
    if save_all_data(st.session_state.df_working):
        st.session_state.df_saved = st.session_state.df_working.copy()
        st.session_state.has_unsaved_changes = False
        st.sidebar.success("✅ All changes saved to CSV!")
        st.balloons()
        st.rerun()
    else:
        st.sidebar.error("❌ Save failed")

# Download CSV button
if len(st.session_state.df_working) > 0:
    csv_data = st.session_state.df_working.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Download CSV (All Days)",
        data=csv_data,
        file_name="prempeh_library_all_data.csv",
        mime="text/csv",
        use_container_width=True
    )

# Sync to Google Sheet button
if len(st.session_state.df_working) > 0:
    csv_data = st.session_state.df_working.to_csv(index=False)
    st.sidebar.download_button(
        label="☁️ CSV for Google Sheet",
        data=csv_data,
        file_name="prempeh_library_all_data.csv",
        mime="text/csv",
        use_container_width=True
    )

# Discard button
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
    
    # Date selector
    col1, col2 = st.columns(2)
    with col1:
        actual_date = st.date_input("Select Date", datetime.now())
    with col2:
        selected_day = actual_date.strftime("%A")
        st.write(f"**Day:** {selected_day}")
    
    date_str = actual_date.strftime("%Y-%m-%d")
    
    # Check if data exists in working dataframe
    existing_data = st.session_state.df_working[st.session_state.df_working["date"] == date_str] if len(st.session_state.df_working) > 0 else pd.DataFrame()
    
    if len(existing_data) > 0:
        st.info(f"📌 Data EXISTS for {selected_day}. Edit below.")
    else:
        st.info(f"✨ No data yet for {selected_day}. Enter new data below.")
    
    st.write(f"### 📅 {selected_day}, {actual_date.strftime('%B %d, %Y')}")
    
    # Create lookup for existing values
    lookup = {}
    if len(existing_data) > 0:
        for _, row in existing_data.iterrows():
            lookup[(row['time_slot'], row['floor'])] = row['count']
    
    # Data entry grid
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
    
    # Calculate column totals
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
    
    # Stage button
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
    
    # Show current working data summary
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
    st.title("🏛️ Prempeh II Library - Executive Dashboard")
    st.caption("View all data (including staged unsaved changes)")
    
    display_df = st.session_state.df_working
    
    if len(display_df) == 0:
        st.warning("No data yet. Add data in 'Add/Edit Days' page.")
        st.stop()
    
    temp_df = display_df.copy()
    temp_df['date_obj'] = pd.to_datetime(temp_df['date'])
    temp_df['month_year'] = temp_df['date_obj'].dt.strftime('%B %Y')
    temp_df['weekday'] = temp_df['date_obj'].dt.day_name()
    
    available_months = sorted(temp_df['month_year'].unique(), reverse=True)
    selected_month = st.selectbox("📅 Select Month", available_months)
    
    df = temp_df[temp_df['month_year'] == selected_month]
    
    if len(df) == 0:
        st.warning(f"No data for {selected_month}")
        st.stop()
    
    total_visitors = df['count'].sum()
    days_active = df['date'].nunique()
    avg_daily = total_visitors / days_active if days_active > 0 else 0
    
    daily_totals = df.groupby('date_obj')['count'].sum()
    busiest_day = daily_totals.idxmax().strftime('%A, %B %d') if len(daily_totals) > 0 else "N/A"
    busiest_day_count = daily_totals.max() if len(daily_totals) > 0 else 0
    busiest_floor = df.groupby('floor')['count'].sum().idxmax()
    busiest_time = df.groupby('time_slot')['count'].sum().idxmax()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Visitors", f"{total_visitors:,}")
    col2.metric("Days Active", days_active)
    col3.metric("Avg Daily", f"{avg_daily:.0f}")
    col4.metric("Busiest Day", busiest_day[:15], f"{busiest_day_count} visitors")
    col5.metric("Peak Floor", busiest_floor[:12])
    
    st.divider()
    
    st.subheader(f"📈 Daily Traffic Trend - {selected_month}")
    daily_trend = df.groupby('date_obj')['count'].sum().reset_index()
    if len(daily_trend) > 0:
        fig1 = px.line(daily_trend, x='date_obj', y='count', markers=True)
        fig1.add_hline(y=daily_trend['count'].mean(), line_dash="dash", annotation_text=f"Monthly Avg: {daily_trend['count'].mean():.0f}")
        st.plotly_chart(fig1, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Total by Floor")
        floor_total = df.groupby('floor')['count'].sum().sort_values(ascending=True)
        fig2 = px.bar(x=floor_total.values, y=floor_total.index, orientation='h')
        st.plotly_chart(fig2, use_container_width=True)
        floor_pct = (floor_total / floor_total.sum() * 100).round(1)
        st.caption("**Floor Distribution:**")
        for floor, pct in floor_pct.items():
            st.write(f"   - {floor}: {pct}%")
    
    with col2:
        st.subheader("⏰ Total by Time Slot")
        time_total = df.groupby('time_slot')['count'].sum().reindex(time_slots)
        fig3 = px.bar(x=time_total.index, y=time_total.values)
        st.plotly_chart(fig3, use_container_width=True)
        time_pct = (time_total / time_total.sum() * 100).round(1)
        st.caption("**Time Distribution:**")
        for time, pct in time_pct.items():
            st.write(f"   - {time}: {pct}%")
    
    st.subheader("🔥 Floor vs Time Heatmap")
    pivot = df.groupby(['floor', 'time_slot'])['count'].sum().unstack()
    pivot = pivot.reindex(columns=time_slots)
    fig4 = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="YlOrRd")
    st.plotly_chart(fig4, use_container_width=True)
    
    st.subheader("📅 Weekly Pattern")
    weekly_pattern = df.groupby('weekday')['count'].sum().reindex(days_order)
    fig5 = px.bar(x=weekly_pattern.index, y=weekly_pattern.values)
    st.plotly_chart(fig5, use_container_width=True)
    
    st.subheader("📋 Daily Totals")
    daily_summary = df.groupby(['date_obj', 'weekday'])['count'].sum().reset_index()
    daily_summary.columns = ['Date', 'Day', 'Total Visitors']
    daily_summary['Date'] = daily_summary['Date'].dt.strftime('%B %d')
    daily_summary['Rank'] = daily_summary['Total Visitors'].rank(ascending=False).astype(int)
    st.dataframe(daily_summary.sort_values('Date'), use_container_width=True)
    
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
