import os
import json


DIR_NAME = os.path.dirname(__file__)
FILE_NAME = os.path.join(DIR_NAME, "config.json")


def read_file():
    with open(FILE_NAME) as file:
        data = json.load(file)
    return data


def get_daily_candles_dir() -> str:
    return read_file()["candles_daily"]


def get_intraday_candles_dir() -> str:
    return read_file()["candles_intraday"]


def get_news_dir() -> str:
    return read_file()["news"]


def get_snapshot_dir() -> str:
    return read_file()["snapshots"]


def get_statements_dir() -> str:
    return read_file()["statements"]
