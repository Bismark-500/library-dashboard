import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Prempeh II Library", layout="wide")

# ========== DEFINE ALL CONSTANTS ==========
floors = ["Ground floor", "First floor", "Second floor", "Third floor", "Fourth floor", "Research Commons"]
time_slots = ["11am", "2pm", "4pm", "8pm"]
days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Local CSV file
LOCAL_DATA_FILE = "prempeh_library_all_data.csv"

# ========== LOAD DATA ==========
def load_all_data():
    if os.path.exists(LOCAL_DATA_FILE):
        df = pd.read_csv(LOCAL_DATA_FILE)
        return df
    return pd.DataFrame(columns=["date", "day", "floor", "time_slot", "count"])

def save_all_data(df):
    df.to_csv(LOCAL_DATA_FILE, index=False)
    return True

df_all = load_all_data()

# ========== SIDEBAR ==========
st.sidebar.title("🏛️ Prempeh II Library")
st.sidebar.caption("Complete Analytics System")

if len(df_all) > 0:
    total_visitors = df_all['count'].sum()
    total_days = df_all['date'].nunique()
    st.sidebar.success(f"✅ {total_days} days • {total_visitors:,} visitors")
    
    # Show available months
    if 'date' in df_all.columns:
        df_all['date_obj'] = pd.to_datetime(df_all['date'])
        df_all['month_year'] = df_all['date_obj'].dt.strftime('%B %Y')
        available_months = sorted(df_all['month_year'].unique(), reverse=True)
        with st.sidebar.expander("📅 Data by Month"):
            for m in available_months:
                month_total = df_all[df_all['month_year'] == m]['count'].sum()
                st.sidebar.write(f"   - {m}: {month_total:,} visitors")
else:
    st.sidebar.info("📝 No data yet. Add your first day!")

if st.sidebar.button("☁️ Download CSV for Cloud"):
    if len(df_all) > 0:
        csv_data = df_all.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="prempeh_library_all_data.csv",
            mime="text/csv"
        )

page = st.sidebar.radio("Navigate:", ["📝 Enter Data", "✏️ Edit Data", "📊 Executive Dashboard", "📅 Daily View", "📄 Export Report"])

# ========== DATA ENTRY PAGE ==========
if page == "📝 Enter Data":
    st.title("🏛️ Prempeh II Library - Enter Data")
    
    col1, col2 = st.columns(2)
    with col1:
        actual_date = st.date_input("Select Date", datetime.now())
    with col2:
        selected_day = actual_date.strftime("%A")
        st.write(f"**Day:** {selected_day}")
    
    date_str = actual_date.strftime("%Y-%m-%d")
    existing_for_date = df_all[df_all["date"] == date_str] if len(df_all) > 0 else pd.DataFrame()
    
    if len(existing_for_date) > 0:
        st.warning(f"⚠️ Data already exists for {actual_date}. Use 'Edit Data' to modify.")
    
    st.write(f"### 📅 {selected_day}, {actual_date.strftime('%B %d, %Y')}")
    
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
            key = f"{date_str}_{time_slot}_{floor}"
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
    total_cols[0].write("**Total for this day**")
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
                    "date": date_str,
                    "day": selected_day,
                    "floor": floor,
                    "time_slot": time_slot,
                    "count": count
                })
        
        new_df = pd.DataFrame(new_rows)
        
        if len(df_all) > 0:
            df_all = df_all[df_all["date"] != date_str]
            df_all = pd.concat([df_all, new_df], ignore_index=True)
        else:
            df_all = new_df
        
        save_all_data(df_all)
        st.success(f"✅ Data for {selected_day} SAVED!")
        st.balloons()
        st.rerun()

# ========== EDIT DATA PAGE ==========
elif page == "✏️ Edit Data":
    st.title("✏️ Edit Existing Data")
    
    if len(df_all) == 0:
        st.warning("No data to edit.")
        st.stop()
    
    all_dates = sorted(df_all["date"].unique(), reverse=True)
    selected_date_str = st.selectbox("Select date to edit", all_dates)
    
    date_data = df_all[df_all["date"] == selected_date_str]
    
    if len(date_data) > 0:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")
        st.write(f"### Editing {selected_date.strftime('%A, %B %d, %Y')}")
        
        day_name = date_data['day'].iloc[0]
        edited_data = {}
        
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
                existing = date_data[(date_data["time_slot"] == time_slot) & (date_data["floor"] == floor)]["count"].values
                existing_val = existing[0] if len(existing) > 0 else 0
                
                key = f"edit_{selected_date_str}_{time_slot}_{floor}"
                count = row_cols[i+1].number_input(
                    "", min_value=0, step=1, key=key, 
                    label_visibility="collapsed",
                    value=int(existing_val)
                )
                edited_data[(time_slot, floor)] = count
                row_total += count
                floor_totals[floor] += count
            
            row_cols[-1].write(f"**{row_total}**")
        
        st.markdown("---")
        total_cols = st.columns([1.2] + [1]*len(floors) + [1.2])
        total_cols[0].write("**Total for this day**")
        grand_total = 0
        for i, floor in enumerate(floors):
            total_cols[i+1].write(f"**{floor_totals[floor]}**")
            grand_total += floor_totals[floor]
        total_cols[-1].write(f"**{grand_total}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 SAVE CHANGES", type="primary"):
                new_rows = []
                for time_slot in time_slots:
                    for floor in floors:
                        new_rows.append({
                            "date": selected_date_str,
                            "day": day_name,
                            "floor": floor,
                            "time_slot": time_slot,
                            "count": edited_data.get((time_slot, floor), 0)
                        })
                
                new_df = pd.DataFrame(new_rows)
                df_all = df_all[df_all["date"] != selected_date_str]
                df_all = pd.concat([df_all, new_df], ignore_index=True)
                save_all_data(df_all)
                st.success("✅ Changes saved!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ DELETE THIS DAY"):
                df_all = df_all[df_all["date"] != selected_date_str]
                save_all_data(df_all)
                st.success("✅ Data deleted!")
                st.rerun()

# ========== EXECUTIVE DASHBOARD (RICH VERSION) ==========
elif page == "📊 Executive Dashboard":
    st.title("🏛️ Prempeh II Library - Executive Dashboard")
    st.caption("Complete Analytics & Insights")
    
    if len(df_all) == 0:
        st.warning("No data yet.")
        st.stop()
    
    # Prepare data
    df_all['date_obj'] = pd.to_datetime(df_all['date'])
    df_all['month'] = df_all['date_obj'].dt.strftime('%B')
    df_all['year'] = df_all['date_obj'].dt.year
    df_all['month_year'] = df_all['date_obj'].dt.strftime('%B %Y')
    df_all['weekday'] = df_all['date_obj'].dt.day_name()
    
    # Month selector
    available_months = sorted(df_all['month_year'].unique(), reverse=True)
    selected_month = st.selectbox("📅 Select Month", available_months)
    
    # Filter data
    df = df_all[df_all['month_year'] == selected_month]
    
    if len(df) == 0:
        st.warning(f"No data for {selected_month}")
        st.stop()
    
    # ========== TOP KPI ROW ==========
    st.subheader(f"📊 {selected_month} - Key Performance Indicators")
    
    total_visitors = df['count'].sum()
    days_active = df['date'].nunique()
    avg_daily = total_visitors / days_active if days_active > 0 else 0
    
    # Find busiest day
    daily_totals = df.groupby('date_obj')['count'].sum()
    busiest_day = daily_totals.idxmax().strftime('%A, %B %d')
    busiest_day_count = daily_totals.max()
    
    # Find busiest floor and time
    busiest_floor = df.groupby('floor')['count'].sum().idxmax()
    busiest_time = df.groupby('time_slot')['count'].sum().idxmax()
    
    # Calculate growth (if previous month exists)
    growth = "N/A"
    month_index = available_months.index(selected_month)
    if month_index + 1 < len(available_months):
        prev_month = available_months[month_index + 1]
        prev_total = df_all[df_all['month_year'] == prev_month]['count'].sum()
        if prev_total > 0:
            growth_pct = ((total_visitors - prev_total) / prev_total) * 100
            growth = f"{growth_pct:+.1f}%"
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Visitors", f"{total_visitors:,}")
    col2.metric("Days Active", days_active)
    col3.metric("Avg Daily", f"{avg_daily:.0f}")
    col4.metric("Busiest Day", busiest_day[:15], f"{busiest_day_count} visitors")
    col5.metric("Peak Floor", busiest_floor[:12])
    col6.metric("Growth vs Prev", growth)
    
    st.divider()
    
    # ========== DAILY TREND CHART ==========
    st.subheader(f"📈 Daily Traffic Trend - {selected_month}")
    daily_trend = df.groupby('date_obj')['count'].sum().reset_index()
    fig1 = px.line(daily_trend, x='date_obj', y='count', markers=True, 
                   title=f"Daily Visitors in {selected_month}",
                   labels={'date_obj': 'Date', 'count': 'Visitors'})
    fig1.add_hline(y=daily_trend['count'].mean(), line_dash="dash", 
                   annotation_text=f"Monthly Avg: {daily_trend['count'].mean():.0f}")
    # Add max point annotation
    max_point = daily_trend.loc[daily_trend['count'].idxmax()]
    fig1.add_annotation(x=max_point['date_obj'], y=max_point['count'],
                        text=f"Peak: {max_point['count']}", showarrow=True, arrowhead=1)
    st.plotly_chart(fig1, use_container_width=True)
    
    # ========== TWO COLUMN CHARTS ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Total by Floor")
        floor_total = df.groupby('floor')['count'].sum().sort_values(ascending=True)
        colors = ['#2ecc71' if i == floor_total.idxmax() else '#3498db' for i in floor_total.index]
        fig2 = px.bar(x=floor_total.values, y=floor_total.index, orientation='h',
                     title=f"Floor Usage in {selected_month}",
                     labels={'x': 'Total Visitors', 'y': ''})
        fig2.update_traces(marker_color=colors)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Also show floor percentages
        floor_pct = (floor_total / floor_total.sum() * 100).round(1)
        st.caption("**Floor Distribution:**")
        for floor, pct in floor_pct.items():
            st.write(f"   - {floor}: {pct}%")
    
    with col2:
        st.subheader("⏰ Total by Time Slot")
        time_total = df.groupby('time_slot')['count'].sum().reindex(time_slots)
        colors = ['#e74c3c' if i == time_total.idxmax() else '#3498db' for i in time_total.index]
        fig3 = px.bar(x=time_total.index, y=time_total.values,
                     title=f"Time Slot Usage in {selected_month}",
                     labels={'x': 'Time', 'y': 'Total Visitors'})
        fig3.update_traces(marker_color=colors)
        st.plotly_chart(fig3, use_container_width=True)
        
        # Time slot percentages
        time_pct = (time_total / time_total.sum() * 100).round(1)
        st.caption("**Time Distribution:**")
        for time, pct in time_pct.items():
            st.write(f"   - {time}: {pct}%")
    
    st.divider()
    
    # ========== HEATMAPS ==========
    st.subheader("🔥 Advanced Analytics")
    
    heat1, heat2 = st.columns(2)
    
    with heat1:
        st.caption("Floor × Time Slot Heatmap")
        pivot = df.groupby(['floor', 'time_slot'])['count'].sum().unstack()
        pivot = pivot.reindex(columns=time_slots)
        fig4 = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="YlOrRd",
                         title="Which floor is busy at which time?")
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
    
    with heat2:
        st.caption("Day × Time Slot Heatmap")
        day_pivot = df.groupby(['weekday', 'time_slot'])['count'].sum().unstack()
        day_pivot = day_pivot.reindex(columns=time_slots)
        day_pivot = day_pivot.reindex([d for d in days_order if d in day_pivot.index])
        fig5 = px.imshow(day_pivot, text_auto=True, aspect="auto", color_continuous_scale="YlOrRd",
                         title="Which day is busy at which time?")
        fig5.update_layout(height=400)
        st.plotly_chart(fig5, use_container_width=True)
    
    # ========== WEEKLY PATTERN ==========
    st.subheader("📅 Weekly Pattern Analysis")
    
    weekly_pattern = df.groupby('weekday')['count'].sum().reindex(days_order)
    fig6 = px.bar(x=weekly_pattern.index, y=weekly_pattern.values,
                  title=f"Weekly Traffic Pattern - {selected_month}",
                  labels={'x': 'Day', 'y': 'Total Visitors'})
    fig6.update_traces(marker_color='#3498db')
    st.plotly_chart(fig6, use_container_width=True)
    
    # ========== DAILY TOTALS TABLE ==========
    st.subheader("📋 Daily Totals")
    
    # Create daily summary table
    daily_summary = df.groupby(['date_obj', 'weekday'])['count'].sum().reset_index()
    daily_summary.columns = ['Date', 'Day', 'Total Visitors']
    daily_summary['Date'] = daily_summary['Date'].dt.strftime('%B %d')
    
    # Add rank
    daily_summary['Rank'] = daily_summary['Total Visitors'].rank(ascending=False).astype(int)
    
    # Highlight busiest day
    st.dataframe(daily_summary.sort_values('Date'), use_container_width=True)
    
    # ========== KEY INSIGHTS ==========
    st.divider()
    st.subheader("📊 Key Insights & Recommendations")
    
    insights = []
    recommendations = []
    
    # Busiest day insight
    busiest_day_name = daily_trend.loc[daily_trend['count'].idxmax(), 'date_obj'].strftime('%A, %B %d')
    insights.append(f"📌 **Peak Day:** {busiest_day_name} was the busiest day with {busiest_day_count:,} visitors")
    
    # Quietest day
    quietest_day_count = daily_trend['count'].min()
    quietest_day_name = daily_trend.loc[daily_trend['count'].idxmin(), 'date_obj'].strftime('%A, %B %d')
    insights.append(f"📌 **Quietest Day:** {quietest_day_name} had {quietest_day_count:,} visitors")
    
    # Peak hour insight
    insights.append(f"📌 **Peak Time:** {busiest_time} is when most people visit")
    
    # Floor insights
    quietest_floor = df.groupby('floor')['count'].sum().idxmin()
    floor_ratio = (floor_total[busiest_floor] / floor_total.sum() * 100).round(1)
    insights.append(f"📌 **Floor Usage:** {busiest_floor} handles {floor_ratio}% of all traffic")
    
    # Recommendations
    if busiest_time in ["4pm", "8pm"]:
        recommendations.append("💡 Consider adding more staff during peak hours")
    
    if floor_ratio > 40:
        recommendations.append("💡 The busiest floor may need more seating or space")
    
    if len(recommendations) == 0:
        recommendations.append("💡 Continue tracking to identify more patterns")
    
    for insight in insights:
        st.write(insight)
    
    st.write("### 💡 Recommendations")
    for rec in recommendations:
        st.write(rec)

# ========== DAILY VIEW PAGE ==========
elif page == "📅 Daily View":
    st.title("📅 Daily Detail View")
    
    if len(df_all) == 0:
        st.warning("No data yet.")
        st.stop()
    
    df_all['date_obj'] = pd.to_datetime(df_all['date'])
    all_dates = sorted(df_all['date_obj'].unique(), reverse=True)
    
    selected_date = st.selectbox("Select a date to view details", all_dates, format_func=lambda x: x.strftime("%A, %B %d, %Y"))
    
    date_data = df_all[df_all['date_obj'] == selected_date]
    
    if len(date_data) > 0:
        st.write(f"### Detailed Breakdown for {selected_date.strftime('%A, %B %d, %Y')}")
        
        daily_total = date_data['count'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Visitors This Day", f"{daily_total:,}")
        
        # Compare to monthly average
        df_all['month_year'] = df_all['date_obj'].dt.strftime('%B %Y')
        current_month = selected_date.strftime('%B %Y')
        month_avg = df_all[df_all['month_year'] == current_month]['count'].sum() / df_all[df_all['month_year'] == current_month]['date'].nunique()
        vs_avg = ((daily_total - month_avg) / month_avg * 100) if month_avg > 0 else 0
        col2.metric("vs Monthly Average", f"{vs_avg:+.1f}%")
        
        # Hourly breakdown table
        st.write("#### Hourly Breakdown by Floor")
        pivot_table = date_data.pivot_table(index="time_slot", columns="floor", values="count", fill_value=0)
        pivot_table["Total"] = pivot_table.sum(axis=1)
        st.dataframe(pivot_table, use_container_width=True)
        
        # Floor totals chart
        st.write("#### Floor Totals")
        floor_totals = date_data.groupby('floor')['count'].sum().sort_values(ascending=False)
        fig = px.bar(x=floor_totals.index, y=floor_totals.values, 
                     title=f"Visitors by Floor on {selected_date.strftime('%B %d')}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Time slot chart
        st.write("#### Time Slot Totals")
        time_totals = date_data.groupby('time_slot')['count'].sum().reindex(time_slots)
        fig2 = px.bar(x=time_totals.index, y=time_totals.values,
                      title=f"Visitors by Time on {selected_date.strftime('%B %d')}")
        st.plotly_chart(fig2, use_container_width=True)

# ========== EXPORT PAGE ==========
else:
    st.title("📄 Export Report")
    
    if len(df_all) == 0:
        st.warning("No data yet.")
        st.stop()
    
    df_all['date_obj'] = pd.to_datetime(df_all['date'])
    df_all['month_year'] = df_all['date_obj'].dt.strftime('%B %Y')
    
    available_months = sorted(df_all['month_year'].unique(), reverse=True)
    selected_month = st.selectbox("Select month to export", available_months)
    
    df_export = df_all[df_all['month_year'] == selected_month]
    
    # Show summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Visitors", f"{df_export['count'].sum():,}")
    col2.metric("Days", df_export['date'].nunique())
    col3.metric("Avg Daily", f"{df_export['count'].sum() / df_export['date'].nunique():.0f}")
    
    # Daily summary table
    st.write("### Daily Summary")
    daily_export = df_export.groupby('date')['count'].sum().reset_index()
    daily_export.columns = ['Date', 'Total Visitors']
    st.dataframe(daily_export, use_container_width=True)
    
    csv_data = df_export.to_csv(index=False)
    
    st.download_button(
        label=f"📥 Download {selected_month} Report (CSV)",
        data=csv_data,
        file_name=f"prempeh_library_{selected_month.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.info("Upload this CSV to Google Sheets to share with your boss.")
