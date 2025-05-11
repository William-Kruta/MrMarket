import os
import pandas as pd
import yfinance as yf
from utils.dates import is_stale
import logging


class Candles:
    def __init__(
        self,
        ticker: str,
        cache_dir: str,
        daily: bool = True,
        period: str = "max",
        log: bool = True,
    ):
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
        self.daily = daily
        self.period = period
        self.log = log
        self.file_path = os.path.join(cache_dir, f"{self.ticker}.csv")
        if self.daily:
            self.interval = "1d"
        else:
            self.interval = "1min"

    def get_candles(self) -> pd.DataFrame:
        df = self._read_file()
        if df.empty:
            df = self._fetch_candles()
            df.to_csv(self.file_path)
            return df
        else:
            index = df.index.to_list()
            stale = is_stale(index[-1], stale_threshold=3)
            if stale:
                new_df = self._fetch_candles()
                new_index = new_df.index.to_list()
                unique_index = list(set(new_index) - set(index))
                unique_data = new_df.loc[unique_index]
                df = pd.concat([df, unique_data], axis=0)
                df.to_csv(self.file_path)
            return df

    def _read_file(self):
        try:
            df = pd.read_csv(self.file_path)
            cols = df.columns.to_list()
            if "Unnamed: 0" in cols:
                df.rename(columns={"Unnamed: 0": "Date"}, inplace=True)
                df.set_index("Date", inplace=True)
            if "Date" in cols:
                df.set_index("Date", inplace=True)
            if self.log:
                logging.info(f"{self.ticker} candles loaded from cache.")
            return df
        except FileNotFoundError as e:
            logging.exception(e)
            return pd.DataFrame()

    def _fetch_candles(self):
        if self.log:
            logging.info(f"Fetching {self.ticker} candles from Yahoo Finance...")

        df = yf.download(
            self.ticker,
            period=self.period,
            interval=self.interval,
            multi_level_index=False,
        )
        return df

    ### Functionality
    def get_spot_price(self):
        candles = self.get_candles()
        return candles["Close"].iloc[-1]
