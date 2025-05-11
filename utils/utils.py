import re
import numpy as np
import pandas as pd
import datetime as dt


def parse_expiration_date(contract_symbol: str) -> str:
    date_pattern = r"(\d{6})[CP]"
    match = re.search(date_pattern, contract_symbol)
    if match:
        expiration_date_yyyymmdd = match.group(1)
        # The format from the symbol is YYMMDD. Let's reconstruct a date string.
        # Assuming the year is in the 2000s based on '25' for 2025.
        year = "20" + expiration_date_yyyymmdd[:2]
        month = expiration_date_yyyymmdd[2:4]
        day = expiration_date_yyyymmdd[4:]
        expiration_date_formatted = f"{year}-{month}-{day}"
        return expiration_date_formatted
    else:
        return ""


def calc_dte(expiration_date, today: str = ""):
    if type(expiration_date) is str:
        expiration_date = dt.datetime.strptime(expiration_date, "%Y-%m-%d").date()
    if today == "":
        today = dt.datetime.now().date()
    else:
        if type(today) is str:
            today = dt.datetime.strptime(today, "%Y-%m-%d").date()
    delta = expiration_date - today
    return delta.days


def handle_growth(values: pd.Series):
    index = 0
    growth = []
    for i, row in values.items():
        if index == 0:
            growth.append(np.nan)
        else:
            last_val = values.iloc[index - 1]
            change = (row - last_val) / last_val * 100
            growth.append(change)
        index += 1
    return growth
