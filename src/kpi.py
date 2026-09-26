import pandas as pd

handled_calls = ['Answered','Transferred']

def kpi_answer_rate(df):
    
    ans_r = df['status'].isin(handled_calls).mean() * 100
    return ans_r

def kpi_abandoned_rate (df):
    
    aban_r = (df['status'] == 'Abandoned').mean() * 100
    return aban_r

def kpi_awt (df):
    awt = df['wait_seconds'].mean() if len(df) > 0 else 0
    return awt.round()

def kpi_aht (df):
    if len(df) > 0 : 
        aht = (df['handle_seconds'].sum() + df['hold_seconds'].sum() + df['after_call_work_seconds'].sum())/len(df)
    else:
        aht = 0
        
    return aht

# two indices for expression customer satisfaction
def kpi_csat_avg(df):
    if df["csat_score"].notna().sum() == 0:
        return 0

    return df["csat_score"].mean()


def kpi_csat_pct(df):
    valid_csat = df["csat_score"].dropna()

    if len(valid_csat) == 0:
        return 0

    return (valid_csat > 3).mean() * 100

def kpi_fcr (df):
    
    filter_df = df[(df['status'] == 'Answered') &(df['first_contact_resolution'] == 'Yes') &(df['transfer_count'] == 0)]
    fcr = (len(filter_df)/ len(df)) * 100 if len(df) > 0 else 0
    return fcr


def calculate_all_kpis(df):
    
    df_handled = df[df['status'].isin(handled_calls)]
    
    return {
        "answer_rate": kpi_answer_rate(df),
        "abandon_rate": kpi_abandoned_rate(df),
        "awt": kpi_awt(df_handled),
        "aht": kpi_aht(df_handled),
        "csat_avg": kpi_csat_avg(df_handled),
        "csat_pct": kpi_csat_pct(df_handled),
        "fcr": kpi_fcr(df_handled)}

def get_kpi_function(kpi):

    functions = {
        "answer_rate": kpi_answer_rate,
        "abandon_rate": kpi_abandoned_rate,
        "awt": kpi_awt,
        "aht": kpi_aht,
        "csat_avg": kpi_csat_avg,
        "csat_pct": kpi_csat_pct,
        "fcr": kpi_fcr}

    if kpi not in functions:
        raise ValueError(f"Unsupported KPI: {kpi}")

    return functions[kpi]

def prepare_kpi_data(df, kpi):

    handled_kpis = {
        "awt",
        "aht",
        "csat_avg",
        "csat_pct",
        "fcr"}

    if kpi in handled_kpis:
        return df[df["status"].isin(handled_calls)]

    return df


def daily_trends(df, kpi):
    target_func = get_kpi_function(kpi)
    data = prepare_kpi_data(df, kpi)

    result = data.groupby("call_date").apply(target_func).to_dict()
    return result



def kpi_by_team(df,kpi):
    target_func = get_kpi_function(kpi)
    data = prepare_kpi_data(df, kpi)

    result = data.groupby("queue").apply(target_func).to_dict()
    return result


def kpi_by_shift(df,kpi):
    target_func = get_kpi_function(kpi)
    data = prepare_kpi_data(df, kpi)

    result = data.groupby("shift_time").apply(target_func).to_dict()
    return result

