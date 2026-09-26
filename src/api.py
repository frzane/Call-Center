from pathlib import Path
import pandas as pd
from datetime import date, datetime
from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel
from kpi import calculate_all_kpis, daily_trends, kpi_by_shift, kpi_by_team

app = FastAPI(title="Call Center KPI API")

# Load cleaned data
DATA_PATH = Path("../data/preprocess/clean_call_center.csv")
df = pd.read_csv(DATA_PATH)

df['call_datetime'] = pd.to_datetime(df['call_datetime'])
df['call_date'] = pd.to_datetime(df['call_date'])




class KPIName(str, Enum):
    answer_rate = "answer_rate"
    abandon_rate = "abandon_rate"
    awt = "awt"
    aht = "aht"
    csat_avg = "csat_avg"
    csat_pct = "csat_pct"
    fcr = "fcr"

class TeamName(str, Enum):
    billing = "Billing"
    sales = "Sales"
    support = "Support"


class ShiftName(str, Enum):
    morning = "Morning"
    afternoon = "Afternoon"
    
class WeekdayName(str, Enum):
    saturday = "Saturday"
    sunday = "Sunday"
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"


@app.get("/")
def root():
    return {"message": "Call Center KPI API is running"}

@app.get("/kpis/summary")
def get_summary(
    team: TeamName | None = None,
    shift: ShiftName | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    weekday: WeekdayName | None = None):


    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400,detail="Start date must be earlier than or equal to End date")
    
    filtered_df = df.copy()

    # Filter data
    if team:
        filtered_df = filtered_df[filtered_df["queue"] == team]

    if shift:
        filtered_df = filtered_df[filtered_df["shift_time"] == shift]

    if date_from:
        filtered_df = filtered_df[filtered_df["call_date"] >= pd.Timestamp(date_from)]

    if date_to:
        filtered_df = filtered_df[filtered_df["call_date"] <= pd.Timestamp(date_to)]

    if weekday:
        filtered_df = filtered_df[filtered_df["week_day"] == weekday]

    # Calculate kpis
    kpis = calculate_all_kpis(filtered_df)

    # Meta information for filtered data
    status = filtered_df["status"]
    
    response = {
              "filters": {
                "team": team,
                "shift": shift,
                "date_from": date_from,
                "date_to": date_to,
                "weekday": weekday
              },
             "kpis": {
                "answer_rate": float(kpis.get("answer_rate", 0) or 0),
                "abandon_rate": float(kpis.get("abandon_rate", 0) or 0),
                "awt": float(kpis.get("awt", 0) or 0),
                "aht": float(kpis.get("aht", 0) or 0),
                "csat_avg": float(kpis.get("csat_avg", 0) or 0),
                "csat_pct": float(kpis.get("csat_pct", 0) or 0),
                "fcr": float(kpis.get("fcr", 0) or 0)},
            "meta": {
                "total_calls": int(status.count()),
                "abandoned_calls": int(status.eq("Abandoned").sum()),
                "handled_calls": int(status.isin(['Answered', 'Transferred']).sum())
                }
            }
    
    return response


def filter_by_date(data,
    date_from: date | None,
    date_to: date | None):

    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400,detail="date_from must be earlier than or equal to date_to" )

    filtered_data = data.copy()

    if date_from:
        filtered_data = filtered_data[filtered_data["call_date"] >= pd.Timestamp(date_from)]

    if date_to:
        filtered_data = filtered_data[filtered_data["call_date"] <= pd.Timestamp(date_to)]

    return filtered_data

@app.get("/kpis/daily")
def get_daily_trend(kpi: KPIName = KPIName.answer_rate,
                date_from: date | None = None,
                date_to: date | None = None,):
    
    filtered_df = filter_by_date(df, date_from, date_to)
    result = daily_trends(filtered_df, kpi.value)

    data = [{"date": str(day.date()),"value": float(value)}
            for day, value in result.items()]

    response = {
              "kpi":kpi.value,
              "filters": {
                "date_from": date_from,
                "date_to": date_to},
              "data": data}
    
    return response


@app.get("/kpis/by-shift")
def compare_shift(kpi: KPIName = KPIName.answer_rate,
                date_from: date | None = None,
                date_to: date | None = None,):

    filtered_df = filter_by_date(df, date_from, date_to)
    result = kpi_by_shift(filtered_df, kpi.value)

    data = [{"shift": shift,"value": float(value)}
            for shift, value in result.items()]

    response = {
              "kpi":kpi.value,
              "filters": {
                "date_from": date_from,
                "date_to": date_to},
              "data": data}
    
    return response


@app.get("/kpis/by-team")
def compare_team(kpi: KPIName = KPIName.answer_rate,
                date_from: date | None = None,
                date_to: date | None = None,):
    
    filtered_df = filter_by_date(df, date_from, date_to)
    result = kpi_by_team(filtered_df, kpi.value)

    data = [{"team": team,"value": float(value)}
            for team, value in result.items()]

    response = {
              "kpi":kpi.value,
              "filters": {
                "date_from": date_from,
                "date_to": date_to},
              "data": data}
    
    return response

    
KPI_LABELS = {
    "answer_rate": "Answer Rate (%)",
    "abandon_rate": "Abandon Rate (%)",
    "awt": "AWT (seconds)",
    "aht": "AHT (seconds)",
    "csat_avg": "CSAT Average",
    "csat_pct": "CSAT % Satisfied",
    "fcr": "FCR (%)"}

@app.get("/filters/options")
def get_options():
    return {
        "teams": ["All", *[team.value for team in TeamName]],
        "shifts": ["All", *[shift.value for shift in ShiftName]],
        "weekdays": ["All", *[day.value for day in WeekdayName]],
        "dates": sorted(df['call_date'].dt.strftime('%Y-%m-%d').unique().tolist()),
        "date_min": df['call_date'].min().strftime('%Y-%m-%d'),
        "date_max": df['call_date'].max().strftime('%Y-%m-%d'),
        "kpis": [
            {"key": key, "label": label}
            for key, label in KPI_LABELS.items()
        ]
    }