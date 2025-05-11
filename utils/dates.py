import datetime as dt


def get_date_delta(date: str, ref_date: str) -> int:
    if type(date) is str:
        date = dt.datetime.strptime(date, "%Y-%m-%d").date()

    if ref_date != "":
        if type(ref_date) is str:
            ref_date = dt.datetime.strptime(ref_date, "%Y-%m-%d")
    else:
        ref_date = dt.datetime.now().date()

    delta = ref_date - date
    return delta.days


def add_days(date: str, days_to_add: int, return_str: bool = True):
    if type(date) is str:
        date = dt.datetime.now().strptime(date, "%Y-%m-%d")

    final_date = date + dt.timedelta(days=days_to_add)
    if return_str:
        final_date = final_date.strftime("%Y-%m-%d")
    return final_date


def is_stale(date: str, ref_date: str = "", stale_threshold: int = 3):
    delta = get_date_delta(date, ref_date)
    if delta >= stale_threshold:
        return True
    else:
        return False


################################################################## Market Timings
def determine_market_time(time_zone: str):
    times = get_market_times(time_zone)
    now = dt.datetime.now().time()

    if now >= times["pre"]["open"] and now < times["pre"]["close"]:
        return "pre"
    elif now >= times["reg"]["open"] and now < times["reg"]["close"]:
        return "reg"
    elif now >= times["post"]["open"] and now < times["post"]["close"]:
        return "post"


def get_market_times(time_zone: str):
    if time_zone.upper() == "PST":
        data = {
            "pre": {"open": dt.time(1), "close": dt.time(6, 30)},
            "reg": {"open": dt.time(6, 30), "close": dt.time(13)},
            "post": {"open": dt.time(13), "close": dt.time(17)},
        }
    return data


def is_pre_market_open(time_zone: str = "PST"):
    now = dt.datetime.now()
    keys = "pre"
    return determine_time(now, keys, time_zone)


def is_market_open(time_zone: str = "PST"):
    now = dt.datetime.now()
    keys = "reg"
    return determine_time(now, keys, time_zone)


def is_post_market_open(time_zone: str = "PST"):
    now = dt.datetime.now()
    keys = "post"
    return determine_time(now, keys, time_zone)


def determine_time(time, key: str, time_zone: str):
    times = get_market_times(time_zone)
    if time.weekday() != 5 and time.weekday() != 6:
        if time.time() >= times[key]["open"] and time.time() < times[key]["close"]:
            return True
        else:
            return False
    else:
        return False


def is_weekend() -> bool:
    weekday = dt.datetime.now().weekday()
    if weekday == 5 or weekday == 6:
        return True
    else:
        return False
