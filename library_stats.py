# ========== PAGE 2: EXECUTIVE DASHBOARD (BEAUTIFUL VERSION) ==========
elif page == "📊 Executive Dashboard":
    st.title("🏛️ Prempeh II Library")
    st.caption("Executive Dashboard - Real-time Library Analytics")
    
    display_df = st.session_state.df_working
    
    if len(display_df) == 0:
        st.warning("No data yet. Add data in 'Add/Edit Days' page.")
        st.stop()
    
    temp_df = display_df.copy()
    temp_df['date_obj'] = pd.to_datetime(temp_df['date'])
    temp_df['month_year'] = temp_df['date_obj'].dt.strftime('%B %Y')
    temp_df['weekday'] = temp_df['date_obj'].dt.day_name()
    
    available_months = sorted(temp_df['month_year'].unique(), reverse=True)
    selected_month = st.selectbox("📅 Select Month", available_months, key="dashboard_month")
    
    df = temp_df[temp_df['month_year'] == selected_month]
    
    if len(df) == 0:
        st.warning(f"No data for {selected_month}")
        st.stop()
    
    # ========== KPI CARDS ROW (BEAUTIFUL) ==========
    total_visitors = df['count'].sum()
    days_active = df['date'].nunique()
    avg_daily = total_visitors / days_active if days_active > 0 else 0
    
    daily_totals = df.groupby('date_obj')['count'].sum()
    busiest_day = daily_totals.idxmax().strftime('%A, %B %d') if len(daily_totals) > 0 else "N/A"
    busiest_day_count = daily_totals.max() if len(daily_totals) > 0 else 0
    
    busiest_floor = df.groupby('floor')['count'].sum().idxmax()
    busiest_time = df.groupby('time_slot')['count'].sum().idxmax()
    
    # Calculate growth (if previous month exists)
    available_months_list = sorted(temp_df['month_year'].unique(), reverse=True)
    growth = "N/A"
    month_index = available_months_list.index(selected_month)
    if month_index + 1 < len(available_months_list):
        prev_month = available_months_list[month_index + 1]
        prev_total = temp_df[temp_df['month_year'] == prev_month]['count'].sum()
        if prev_total > 0:
            growth_pct = ((total_visitors - prev_total) / prev_total) * 100
            growth = f"{growth_pct:+.1f}%"
    
    # Create beautiful KPI cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; text-align: center; color: white;'>
            <p style='font-size: 12px; margin: 0; opacity: 0.8;'>📊 TOTAL VISITORS</p>
            <h2 style='font-size: 28px; margin: 5px 0;'>""" + f"{total_visitors:,}" + """</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 15px; border-radius: 10px; text-align: center; color: white;'>
            <p style='font-size: 12px; margin: 0; opacity: 0.8;'>📅 DAYS ACTIVE</p>
            <h2 style='font-size: 28px; margin: 5px 0;'>""" + f"{days_active}" + """</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 15px; border-radius: 10px; text-align: center; color: white;'>
            <p style='font-size: 12px; margin: 0; opacity: 0.8;'>📈 AVERAGE DAILY</p>
            <h2 style='font-size: 28px; margin: 5px 0;'>""" + f"{avg_daily:.0f}" + """</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 15px; border-radius: 10px; text-align: center; color: #1a2332;'>
            <p style='font-size: 12px; margin: 0; opacity: 0.8;'>🏆 BUSIEST DAY</p>
            <h4 style='font-size: 14px; margin: 5px 0;'>""" + f"{busiest_day[:12]}" + """</h4>
            <p style='font-size: 12px; margin: 0;'>""" + f"{busiest_day_count} visitors" + """</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 15px; border-radius: 10px; text-align: center; color: #1a2332;'>
            <p style='font-size: 12px; margin: 0; opacity: 0.8;'>🏢 PEAK FLOOR</p>
            <h4 style='font-size: 14px; margin: 5px 0;'>""" + f"{busiest_floor[:12]}" + """</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 15px; border-radius: 10px; text-align: center; color: #1a2332;'>
            <p style='font-size: 12px; margin: 0; opacity: 0.8;'>⏰ PEAK TIME</p>
            <h4 style='font-size: 14px; margin: 5px 0;'>""" + f"{busiest_time}" + """</h4>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== GROWTH INDICATOR ==========
    if growth != "N/A":
        if float(growth.strip('%')) > 0:
            st.success(f"📈 **Growth:** {growth} increase compared to previous month")
        elif float(growth.strip('%')) < 0:
            st.warning(f"📉 **Decline:** {growth} decrease compared to previous month")
        else:
            st.info(f"📊 **Stable:** No significant change compared to previous month")
    
    st.divider()
    
    # ========== DAILY TREND CHART ==========
    st.subheader(f"📈 Daily Traffic Trend - {selected_month}")
    daily_trend = df.groupby('date_obj')['count'].sum().reset_index()
    if len(daily_trend) > 0:
        fig1 = px.line(daily_trend, x='date_obj', y='count', markers=True,
                       color_discrete_sequence=['#667eea'])
        fig1.update_traces(line=dict(width=3), marker=dict(size=8))
        fig1.add_hline(y=daily_trend['count'].mean(), line_dash="dash", 
                       annotation_text=f"Monthly Avg: {daily_trend['count'].mean():.0f}",
                       line_color="#764ba2")
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # ========== TWO COLUMN CHARTS ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Total by Floor")
        floor_total = df.groupby('floor')['count'].sum().sort_values(ascending=True)
        colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b']
        fig2 = px.bar(x=floor_total.values, y=floor_total.index, orientation='h',
                     color_discrete_sequence=colors[:len(floor_total)])
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Floor percentages
        floor_pct = (floor_total / floor_total.sum() * 100).round(1)
        st.caption("**📊 Floor Distribution:**")
        for floor, pct in floor_pct.items():
            st.write(f"   - {floor}: {pct}%")
    
    with col2:
        st.subheader("⏰ Total by Time Slot")
        time_total = df.groupby('time_slot')['count'].sum().reindex(time_slots)
        colors = ['#4facfe', '#43e97b', '#fa709a', '#f093fb']
        fig3 = px.bar(x=time_total.index, y=time_total.values,
                     color_discrete_sequence=colors[:len(time_total)])
        fig3.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Time percentages
        time_pct = (time_total / time_total.sum() * 100).round(1)
        st.caption("**📊 Time Distribution:**")
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
        fig4 = px.imshow(pivot, text_auto=True, aspect="auto", 
                        color_continuous_scale="YlOrRd",
                        labels={'x': 'Time Slot', 'y': 'Floor', 'color': 'Visitors'})
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
    
    with heat2:
        st.caption("Day × Time Slot Heatmap")
        day_pivot = df.groupby(['weekday', 'time_slot'])['count'].sum().unstack()
        day_pivot = day_pivot.reindex(columns=time_slots)
        day_pivot = day_pivot.reindex([d for d in days_order if d in day_pivot.index])
        fig5 = px.imshow(day_pivot, text_auto=True, aspect="auto", 
                        color_continuous_scale="YlOrRd",
                        labels={'x': 'Time Slot', 'y': 'Day', 'color': 'Visitors'})
        fig5.update_layout(height=400)
        st.plotly_chart(fig5, use_container_width=True)
    
    # ========== WEEKLY PATTERN ==========
    st.subheader("📅 Weekly Pattern Analysis")
    weekly_pattern = df.groupby('weekday')['count'].sum().reindex(days_order)
    colors = ['#667eea', '#4facfe', '#43e97b', '#f093fb', '#fa709a']
    fig6 = px.bar(x=weekly_pattern.index, y=weekly_pattern.values,
                 color_discrete_sequence=colors[:len(weekly_pattern)])
    fig6.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    )
    st.plotly_chart(fig6, use_container_width=True)
    
    # ========== KEY INSIGHTS ==========
    st.divider()
    st.subheader("📊 Key Insights")
    
    insights = []
    
    # Busiest day insight
    if len(daily_totals) > 0:
        busiest_day_name = daily_totals.idxmax().strftime('%A, %B %d')
        insights.append(f"📌 **Peak Day:** {busiest_day_name} was the busiest day with {busiest_day_count:,} visitors")
        
        quietest_day_count = daily_totals.min()
        quietest_day_name = daily_totals.idxmin().strftime('%A, %B %d')
        insights.append(f"📌 **Quietest Day:** {quietest_day_name} had {quietest_day_count:,} visitors")
    
    # Peak time insight
    insights.append(f"📌 **Peak Time:** {busiest_time} is when most people visit")
    
    # Floor insights
    quietest_floor = df.groupby('floor')['count'].sum().idxmin()
    floor_ratio = (df.groupby('floor')['count'].sum()[busiest_floor] / df['count'].sum() * 100).round(1)
    insights.append(f"📌 **Floor Usage:** {busiest_floor} handles {floor_ratio}% of all traffic")
    
    # Daily average insight
    insights.append(f"📌 **Average Daily:** {avg_daily:.0f} visitors per day")
    
    # Recommendations
    st.write("### 💡 Recommendations")
    if busiest_time in ["4pm", "8pm"]:
        st.info("💡 Consider adding more staff during peak hours")
    if floor_ratio > 40:
        st.info("💡 The busiest floor may need more seating or space")
    if days_active < 5:
        st.info("💡 Consider collecting data for more days to identify patterns")
    if len(insights) == 0:
        st.info("💡 Continue tracking to identify more patterns")
    
    for insight in insights:
        st.write(insight)
    
    if st.session_state.has_unsaved_changes:
        st.warning("⚠️ You have unsaved changes. The dashboard shows UNSAVED data. Click 'SAVE ALL CHANGES' in sidebar to save to CSV.")
