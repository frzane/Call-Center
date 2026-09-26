# Call center dashboard
import streamlit as st
import requests
from datetime import date


import time
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


def get_api(endpoint, params=None):
    
    response = requests.get(
        f"{API_URL}{endpoint}",
        params=params)

    response.raise_for_status()

    return response.json()

def show_summary_kpis(data): 
    meta = data["meta"]
    kpis = data["kpis"]
    
    # Row 1 — Call volume
    col1, col2, col3 = st.columns(3, border=True)
    
    with col1:
        st.metric("Total Calls",meta["total_calls"])
    
    with col2:
        st.metric("Handled Calls",meta["handled_calls"])
    
    with col3:
        st.metric("Abandoned Calls",meta["abandoned_calls"])
    
    st.divider()
    
    # Row 2 — KPIs
    col1, col2, col3 = st.columns(3, border=True)
    
    with col1:
        st.metric("Answer Rate",f"{kpis['answer_rate']:.1f}%" )
    
    with col2:
        st.metric("Abandon Rate",f"{kpis['abandon_rate']:.1f}%" )
    
    with col3:
        st.metric("AWT",f"{kpis['awt']:.0f} sec" )
    
    
    # Row 3 — KPIs
    col1, col2, col3 = st.columns(3, border=True)
    
    with col1:
        st.metric( "AHT", f"{kpis['aht']:.0f} sec")
    
    with col2:
        st.metric( "CSAT Average",f"{kpis['csat_avg']:.1f} / 5")
        st.caption(f"Satisfied: {kpis['csat_pct']:.1f}%")
    
    with col3:
        st.metric( "FCR",f"{kpis['fcr']:.1f}%" )

    
def display_kpi_summary(options):

   
    # Filter option for kpis
    st.sidebar.title('Filter')
    selected_team = st.sidebar.selectbox("Team", options.get('teams'))
    selected_shift = st.sidebar.selectbox("Shift",  options.get('shifts'))
    selected_week_day = st.sidebar.selectbox("Week day",  options.get('weekdays'))
    
    min_date = date.fromisoformat(options["date_min"])
    max_date = date.fromisoformat(options["date_max"])
    
    selected_dates = st.sidebar.date_input("Date range",value=(min_date, max_date),
                                            min_value=min_date ,max_value=max_date)

    #assign selected filter
    params = {}
    if selected_team  and selected_team != "All":
        params["team"] = selected_team
    
    if selected_shift and selected_shift != "All":
        params["shift"] = selected_shift
    
    if selected_week_day and selected_week_day != "All":
        params["weekday"] = selected_week_day
    
    if len(selected_dates) >= 2:
        date_from, date_to = selected_dates
        params["date_from"] = date_from
        params["date_to"] = date_to

    elif len(selected_dates) == 1:
        date_from = selected_dates[0]
        params["date_from"] = date_from
        params["date_to"] = date_from

    # get new data

    data = get_api("/kpis/summary", params)
    show_summary_kpis(data)


def display_calendar(key):
    
    min_date = date.fromisoformat(options["date_min"])
    max_date = date.fromisoformat(options["date_max"])

    selected_dates = st.date_input("Date range",value=(min_date, max_date),
                                            min_value=min_date ,max_value=max_date,
                                            key=f"date_range_{key}")

    if len(selected_dates) >= 2:
        date_from, date_to = selected_dates

    elif len(selected_dates) == 1:
        date_from = selected_dates[0]
        date_to = selected_dates[0]
    else: 
        date_from, date_to = min_date, max_date

    return date_from,date_to


def kpis_fiter(kpis, section_key):
    col1, col2 = st.columns(2)
    with col1:
        start_date, end_date = display_calendar(section_key)
    
    with col2:
        selected_kpi = st.selectbox("KPIs", options=kpis, format_func=lambda x: x["label"], key=f"kpi_{section_key}")

    return start_date, end_date, selected_kpi["key"]
    

SHIFT_COLORS = {
    "Morning": "#4E79A7",
    "Afternoon": "#F28E2B"}
def show_bar_chart_shift(kpi, date_from, date_to):

    params = {
        "kpi": kpi,
        "date_from": date_from,
        "date_to": date_to
    }

    response = get_api("/kpis/by-shift", params)

    data = pd.DataFrame(response["data"])

    fig = px.bar(data,  x="shift", y="value", text_auto=".2f", color="shift", color_discrete_map=SHIFT_COLORS)

    fig.update_layout(showlegend=False, coloraxis_showscale=False, template="plotly_white")

    fig.update_xaxes(type="category")

    st.plotly_chart(fig, use_container_width=True)
    
TEAM_COLORS = {
    "Billing": "#4E79A7",
    "Sales": "#F28E2B",
    "Support": "#59A14F"}    
def show_bar_chart_team(kpi, date_from, date_to):

    params = {
        "kpi": kpi,
        "date_from": date_from,
        "date_to": date_to}

    response = get_api("/kpis/by-team", params)

    data = pd.DataFrame(response["data"])

    fig = px.bar(data, x="team", y="value", text_auto=".2f", color="team", color_discrete_map=TEAM_COLORS)

    fig.update_layout(showlegend=False, coloraxis_showscale=False, template="plotly_white")

    fig.update_xaxes(type="category")

    st.plotly_chart(fig, use_container_width=True)

    
def show_line_chart_daily(kpi, date_from, date_to):

    params = {
        "kpi": kpi,
        "date_from": date_from,
        "date_to": date_to
    }

    response = get_api("/kpis/daily", params)

    data = pd.DataFrame(response["data"])

    fig_trend = go.Figure()

    fig_trend.add_trace(
        go.Scatter(
            name=kpi,
            x=data["date"],
            y=data["value"],
            mode="lines+markers",
            opacity=0.9,
            hovertemplate=("<b>%{x}</b><br>"
                           f"{kpi}: %{{y:.2f}}<extra></extra>"),
            line=dict(color="royalblue",width=1.5),
        )
    )

    fig_trend.update_yaxes(title_text=kpi, title_font=dict(color="royalblue"),
                           tickfont=dict(color="royalblue"), linecolor="royalblue")

    fig_trend.update_layout(
        title=dict(text=f"Daily Trend of {kpi}", x=0.02),
        hovermode="x unified",template="plotly_white")

    st.plotly_chart(fig_trend, use_container_width=True)

    
def display_compare_kpi(options):
    st.sidebar.title("Compare Kpis")
    kpis = options["kpis"]
    
    st.markdown('## Daily trends')
    daily_start_date, daily_end_date, daily_selected_kpi = kpis_fiter(kpis, "daily")
    show_line_chart_daily(daily_selected_kpi,daily_start_date, daily_end_date)
    st.divider()
    
    st.markdown('## KPI by Team')
    team_start_date, team_end_date, team_selected_kpi = kpis_fiter(kpis,'team')
    show_bar_chart_team(team_selected_kpi,team_start_date, team_end_date)
    st.divider()
    
    st.markdown('## KPI by Shift')
    shift_start_date, shift_end_date, shift_selected_kpi = kpis_fiter(kpis,'shift')
    show_bar_chart_shift(shift_selected_kpi,shift_start_date, shift_end_date)
    st.divider()


    # create space above button
    for _ in range(20):
            st.sidebar.write("\n")
    if st.sidebar.button("↻ Refresh data", use_container_width=True):
        
        st.cache_data.clear()
        st.rerun()
     

API_URL = "http://127.0.0.1:8000" 

# configuration app
st.set_page_config(page_title="Call Analysis Dashboard" ,page_icon="📊" , layout="wide")
st.title("Call Center KPIs Dashboard")


              
dashboard_tab = {
    'overview' : ' Overview',
    'compare' : ' Details'
}
   
selected = st.segmented_control(label=" ", options=dashboard_tab.keys(),
                                format_func = lambda x:dashboard_tab.get(x), 
                                default = 'overview')

options = get_api("/filters/options")

if selected == 'overview':
    
    display_kpi_summary(options)
    
    
elif selected == "compare":
    display_compare_kpi(options)

