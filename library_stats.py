import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

st.set_page_config(page_title="Prempeh II Library", layout="wide")

# ========== YOUR GOOGLE SHEET ID ==========
SHEET_ID = "1zrpAi-5tPNIZH8OIViC8wSNmYdDvKtc2L3-BiAn3C4Q"

# Define data structure
floors = ["Ground floor", "First floor", "Second floor", "Third floor", "Fourth floor", "Research Commons"]
time_slots = ["11am", "2pm", "4pm", "8pm"]

# ========== FUNCTION TO LOAD DATA FROM GOOGLE SHEETS ==========
def load_data():
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            
            if len(df) > 0 and 'date' in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                return df
            else:
                return pd.DataFrame(columns=["date", "day", "floor", "time_slot", "count"])
        else:
            return pd.DataFrame(columns=["date", "day", "floor", "time_slot", "count"])
    except Exception as e:
        st.warning(f"Loading data: {e}")
        return pd.DataFrame(columns=["date", "day", "floor", "time_slot", "count"])

# ========== FUNCTION TO SAVE DATA LOCALLY ==========
def save_data_locally(df):
    df.to_csv("prempeh_library_data.csv", index=False)
    st.info("💡 **Next step:** Download this CSV and upload to Google Sheets to update the cloud dashboard.")
    
    csv_data = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV to upload to Google Sheets",
        data=csv_data,
        file_name="prempeh_library_data.csv",
        mime="text/csv"
    )

# Load existing data
df_all = load_data()

# Sidebar
st.sidebar.title("🏛️ Prempeh II Library")
st.sidebar.caption("Senior Data Analytics Dashboard")

if len(df_all) > 0 and 'date' in df_all.columns:
    st.sidebar.success(f"✅ Data loaded: {df_all['date'].nunique()} days")
else:
    st.sidebar.info("📝 No data yet. Add your first day!")

page = st.sidebar.radio("Navigate:", ["📝 Enter Data", "✏️ Edit Data", "📊 Executive Dashboard", "📄 Generate Report"])

# ========== PAGE 1: DATA ENTRY ==========
if page == "📝 Enter Data":
    st.title("🏛️ Prempeh II Library User Statistics")
    st.caption("Enter daily user counts by floor and time")
    
    col1, col2 = st.columns(2)
    with col1:
        actual_date = st.date_input("Select Date", datetime.now())
    with col2:
        selected_day = actual_date.strftime("%A")
        st.write(f"**Day:** {selected_day}")
    
    st.write(f"### 📅 {selected_day}, {actual_date.strftime('%B %d, %Y')}")
    st.info("✨ Only type numbers where people are present. Leave empty for zero.")
    
    entered_data = {}
    
    header_cols = st.columns([1.2] + [1]*len(floors) + [1.2])
    header_cols[0].write("**Time → / Floor ↓**")
    for i, floor in enumerate(floors):
        header_cols[i+1].write(f"**{floor[:12]}**")
    header_cols[-1].write("**Total**")
    
    floor_totals = {floor: 0 for floor in floors}
    
    for time_slot in time_slots:
        row_cols = st.columns([1.2] + [1]*len(floors) + [1.2])
        row_cols[0].write(f"**{time_slot}**")
        
        row_total = 0
        for i, floor in enumerate(floors):
            key = f"{actual_date}_{time_slot}_{floor}"
            count = row_cols[i+1].number_input(
                "", min_value=0, step=1, key=key, 
                label_visibility="collapsed",
                value=None
            )
            count_value = count if count is not None else 0
            entered_data[(time_slot, floor)] = count_value
            row_total += count_value
            floor_totals[floor] += count_value
        
        row_cols[-1].write(f"**{row_total}**")
    
    st.markdown("---")
    total_cols = st.columns([1.2] + [1]*len(floors) + [1.2])
    total_cols[0].write("**Total**")
    grand_total = 0
    for i, floor in enumerate(floors):
        total_cols[i+1].write(f"**{floor_totals[floor]}**")
        grand_total += floor_totals[floor]
    total_cols[-1].write(f"**{grand_total}**")
    
    if st.button("💾 SAVE DATA", type="primary", use_container_width=True):
        new_rows = []
        for time_slot in time_slots:
            for floor in floors:
                count = entered_data.get((time_slot, floor), 0)
                new_rows.append({
                    "date": actual_date.strftime("%Y-%m-%d"),
                    "day": selected_day,
                    "floor": floor,
                    "time_slot": time_slot,
                    "count": count
                })
        
        new_df = pd.DataFrame(new_rows)
        
        if len(df_all) > 0 and 'date' in df_all.columns:
            df_all = df_all[df_all["date"] != pd.to_datetime(actual_date)]
            df_all = pd.concat([df_all, new_df], ignore_index=True)
        else:
            df_all = new_df
        
        save_data_locally(df_all)
        st.success(f"✅ Data prepared for {selected_day}! Download the CSV above.")
        st.balloons()
    
    if len(df_all) > 0 and 'date' in df_all.columns:
        day_data = df_all[df_all["date"] == pd.to_datetime(actual_date)]
        if len(day_data) > 0:
            st.write("### 📋 Currently saved for this date")
            pivot = day_data.pivot_table(index="time_slot", columns="floor", values="count", fill_value=0)
            pivot["Total"] = pivot.sum(axis=1)
            st.dataframe(pivot)

# ========== PAGE 2: EDIT DATA ==========
elif page == "✏️ Edit Data":
    st.title("✏️ Edit Existing Data")
    
    if len(df_all) == 0 or (len(df_all) > 0 and 'date' not in df_all.columns):
        st.warning("No data to edit. Add data first.")
        st.stop()
    
    all_dates = sorted(df_all["date"].unique())
    date_options = [d.date() for d in all_dates]
    
    st.write("### Select date to edit")
    selected_date_obj = st.date_input("Choose a date", date_options[0] if date_options else datetime.now())
    
    selected_date = pd.to_datetime(selected_date_obj)
    date_data = df_all[df_all["date"] == selected_date]
    
    if len(date_data) > 0:
        st.write(f"### Editing {selected_date.strftime('%A, %B %d, %Y')}")
        
        edited_data = {}
        for time_slot in time_slots:
            st.write(f"**{time_slot}**")
            cols = st.columns(len(floors))
            for i, floor in enumerate(floors):
                existing = date_data[(date_data["time_slot"] == time_slot) & (date_data["floor"] == floor)]["count"].values
                existing_val = existing[0] if len(existing) > 0 else 0
                edited_data[(time_slot, floor)] = cols[i].number_input(
                    floor, min_value=0, value=int(existing_val), key=f"edit_{selected_date}_{time_slot}_{floor}"
                )
            st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 SAVE CHANGES", type="primary", use_container_width=True):
                new_rows = []
                for time_slot in time_slots:
                    for floor in floors:
                        new_rows.append({
                            "date": selected_date.strftime("%Y-%m-%d"),
                            "day": selected_date.strftime("%A"),
                            "floor": floor,
                            "time_slot": time_slot,
                            "count": edited_data.get((time_slot, floor), 0)
                        })
                
                new_df = pd.DataFrame(new_rows)
                df_all = df_all[df_all["date"] != selected_date]
                df_all = pd.concat([df_all, new_df], ignore_index=True)
                save_data_locally(df_all)
                st.success("✅ Changes saved! Download the CSV above.")
                st.balloons()
                st.rerun()
        
        with col2:
            if st.button("🗑️ DELETE THIS DAY'S DATA", use_container_width=True):
                df_all = df_all[df_all["date"] != selected_date]
                save_data_locally(df_all)
                st.success("✅ Data deleted! Download the CSV above.")
                st.rerun()
    else:
        st.warning(f"No data found for {selected_date.strftime('%A, %B %d, %Y')}. Try another date.")

# ========== PAGE 3: EXECUTIVE DASHBOARD ==========
elif page == "📊 Executive Dashboard":
    st.title("🏛️ Prempeh II Library - Executive Dashboard")
    st.caption("Senior Data Analytics Report")
    
    if len(df_all) == 0 or (len(df_all) > 0 and 'date' not in df_all.columns):
        st.warning("No data yet. Add data first using 'Enter Data' page.")
        st.stop()
    
    min_date = df_all["date"].min()
    max_date = df_all["date"].max()
    date_range = st.date_input("Date range", [min_date, max_date], key="dashboard_date")
    
    mask = (df_all["date"] >= pd.to_datetime(date_range[0])) & (df_all["date"] <= pd.to_datetime(date_range[1]))
    df = df_all[mask]
    
    if len(df) == 0:
        st.warning("No data in selected range")
        st.stop()
    
    total_visits = df["count"].sum()
    days_counted = df["date"].nunique()
    avg_daily = total_visits / days_counted if days_counted > 0 else 0
    busiest_floor = df.groupby("floor")["count"].sum().idxmax()
    busiest_time = df.groupby("time_slot")["count"].sum().idxmax()
    peak_hour = max(df.groupby("time_slot")["count"].sum().items(), key=lambda x: x[1])[0]
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Visits", f"{total_visits:,}")
    k2.metric("Days", days_counted)
    k3.metric("Avg Daily", f"{avg_daily:.0f}")
    k4.metric("Busiest Floor", busiest_floor[:12])
    k5.metric("Peak Hour", peak_hour)
    
    st.divider()
    
    st.subheader("📈 Daily Traffic Trend")
    daily_total = df.groupby("date")["count"].sum().reset_index()
    fig1 = px.line(daily_total, x="date", y="count", markers=True, title="Total Visitors Per Day")
    if len(daily_total) > 0:
        fig1.add_hline(y=daily_total["count"].mean(), line_dash="dash", annotation_text=f"Average: {daily_total['count'].mean():.0f}")
    st.plotly_chart(fig1, use_container_width=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🏢 Total by Floor")
        floor_total = df.groupby("floor")["count"].sum().sort_values(ascending=True)
        fig2 = px.bar(x=floor_total.values, y=floor_total.index, orientation='h', title="Visitors Per Floor")
        st.plotly_chart(fig2, use_container_width=True)
    
    with c2:
        st.subheader("⏰ Total by Time Slot")
        time_total = df.groupby("time_slot")["count"].sum().reindex(time_slots)
        fig3 = px.bar(x=time_total.index, y=time_total.values, title="Visitors By Time of Day")
        st.plotly_chart(fig3, use_container_width=True)
    
    st.subheader("🔥 Advanced Analytics")
    
    hm1, hm2 = st.columns(2)
    
    with hm1:
        st.caption("Floor Usage by Time Slot")
        pivot = df.groupby(["floor", "time_slot"])["count"].sum().unstack()
        pivot = pivot.reindex(columns=time_slots)
        fig4 = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="YlOrRd")
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
    
    with hm2:
        st.caption("Daily Pattern by Time Slot")
        day_pivot = df.groupby(["day", "time_slot"])["count"].sum().unstack()
        day_pivot = day_pivot.reindex(columns=time_slots)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        day_pivot = day_pivot.reindex([d for d in day_order if d in day_pivot.index])
        fig5 = px.imshow(day_pivot, text_auto=True, aspect="auto", color_continuous_scale="YlOrRd")
        fig5.update_layout(height=400)
        st.plotly_chart(fig5, use_container_width=True)
    
    st.divider()
    st.subheader("📊 Key Insights")
    
    insights = []
    busiest_day_data = df.groupby("day")["count"].sum()
    if len(busiest_day_data) > 0:
        busiest_day = busiest_day_data.idxmax()
        insights.append(f"• **{busiest_day}** is the busiest day of the week")
    
    time_ranking = df.groupby("time_slot")["count"].sum().sort_values(ascending=False)
    if len(time_ranking) > 0:
        insights.append(f"• **{time_ranking.index[0]}** is consistently the busiest time slot")
    
    floor_ranking = df.groupby("floor")["count"].sum().sort_values(ascending=False)
    if len(floor_ranking) > 0:
        insights.append(f"• **{floor_ranking.index[0]}** sees the most traffic")
        if len(floor_ranking) > 1:
            insights.append(f"• **{floor_ranking.index[-1]}** is the quietest area")
    
    for insight in insights:
        st.write(insight)

# ========== PAGE 4: GENERATE REPORT ==========
else:
    st.title("📄 Generate Monthly Report")
    
    if len(df_all) == 0 or (len(df_all) > 0 and 'date' not in df_all.columns):
        st.warning("No data yet. Add data first.")
        st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        report_start = st.date_input("Start date", df_all["date"].min())
    with col2:
        report_end = st.date_input("End date", df_all["date"].max())
    
    df_report = df_all[(df_all["date"] >= pd.to_datetime(report_start)) & (df_all["date"] <= pd.to_datetime(report_end))]
    
    if len(df_report) == 0:
        st.warning("No data in selected period")
        st.stop()
    
    total = df_report["count"].sum()
    days = df_report["date"].nunique()
    
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Report Period", f"{report_start} to {report_end}")
    s2.metric("Total Visits", f"{total:,}")
    s3.metric("Days", days)
    s4.metric("Average Daily", f"{total/days:.0f}" if days > 0 else "0")
    
    if st.button("📊 Export to Excel", type="primary"):
        with pd.ExcelWriter("prempeh_monthly_report.xlsx") as writer:
            df_report.to_excel(writer, sheet_name="Raw Data", index=False)
            df_report.groupby("floor")["count"].sum().to_excel(writer, sheet_name="By Floor")
            df_report.groupby("time_slot")["count"].sum().to_excel(writer, sheet_name="By Time")
            df_report.groupby("date")["count"].sum().to_excel(writer, sheet_name="Daily Total")
        st.success("✅ Excel report saved!")
        st.balloons()
    
    st.info("📁 Files are saved in your 'Prempeh Library' folder")