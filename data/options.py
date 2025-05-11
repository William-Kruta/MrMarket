import os
import math
import numpy as np
import pandas as pd
import yfinance as yf


import datetime as dt

from data.candles import Candles
from utils.utils import parse_expiration_date, calc_dte
from utils.greeks import Greeks, OptionGreeksCalculator


class Options:
    def __init__(
        self,
        ticker: str,
        snapshot_dir: str,
        candle_dir: str,
        use_snapshots: bool = False,
        snapshot_date: str = "",
        FORCE_UPDATE: bool = False,
        yf_obj: yf.Ticker = None,
    ):
        self.ticker = ticker.upper()
        self.snapshot_dir = snapshot_dir
        self.candle_dir = candle_dir
        self.use_snapshots = use_snapshots
        self.snapshot_date = snapshot_date
        self.FORCE_UPDATE = FORCE_UPDATE
        self.ticker_dir = os.path.join(self.snapshot_dir, self.ticker)
        self.greeks = Greeks()
        self.greeks_calc = OptionGreeksCalculator()
        os.makedirs(self.ticker_dir, exist_ok=True)
        os.makedirs(self.candle_dir, exist_ok=True)

        # Class objects
        self.yf_obj = yf_obj
        self.candle_obj = None
        self.risk_free_obj = None
        self.ticker_obj = None
        # Class data
        self.candles = pd.DataFrame()
        self.spot_price = np.nan
        self.objects_set = False
        self.candles_set = False
        self.risk_free_set = False

        self.snapshot_file = "{}_{}.csv"

    def _set_objects(self):
        self.candle_obj = Candles(self.ticker, self.candle_dir)
        self.risk_free_obj = Candles("^TNX", self.candle_dir)
        # Assign yf object if one is not provided to the class on initialization.
        if self.yf_obj is None:
            self.yf_obj = yf.Ticker(self.ticker)
        self.earnings_date = self.yf_obj.info.get("earningsTimestamp", 0)
        self.earnings_date = dt.datetime.fromtimestamp(self.earnings_date)
        self.earnings_date_str = self.earnings_date.strftime("%Y-%m-%d")
        self.expiration_dates = self.yf_obj.options
        self.dividend_yield = self.yf_obj.info.get("dividendYield", 0)
        self.candles = self.candle_obj.get_candles()
        self.spot_price = self.candles["Close"].iloc[-1]
        self.risk_free_candles = self.risk_free_obj.get_candles()
        self.risk_free_rate = self.risk_free_candles["Close"].iloc[-1] / 100

        self.objects_set = True

    def get_options_data(self):
        if not self.objects_set:
            self._set_objects()

        if self.snapshot_date == "":
            path = os.path.join(
                self.ticker_dir,
                self.snapshot_file.format(self.ticker, dt.datetime.now().date()),
            )
        else:
            path = os.path.join(
                self.ticker_dir,
                self.snapshot_file.format(self.ticker, self.snapshot_date),
            )
        if self.FORCE_UPDATE:
            if self.snapshot_date == "":

                data = self._fetch_options_data()
                data.to_csv(path)
            else:  # Protects overwriting previous snapshot with current data.
                pass
        else:
            data = self._read_options_data(path)
            if data.empty:
                data = self._fetch_options_data()
                data.to_csv(path)
        return data

    def _read_options_data(self, path: str):
        try:
            df = pd.read_csv(path)
            return df
        except FileNotFoundError:
            df = pd.DataFrame()
            return df

    def _fetch_options_data(self):
        calls_list, puts_list = [], []
        for exp in self.expiration_dates:
            chain = self.yf_obj.option_chain(exp)
            calls = chain.calls
            puts = chain.puts
            calls["type"] = "call"
            puts["type"] = "put"
            calls_list.append(calls)
            puts_list.append(puts)
        if calls_list:
            data_calls = pd.concat(calls_list, axis=0, ignore_index=True)
        else:
            data_calls = pd.DataFrame()  # Handle case with no call options
        # Concatenate all put dataframes at once
        if puts_list:
            data_puts = pd.concat(puts_list, axis=0, ignore_index=True)
        else:
            data_puts = pd.DataFrame()  # Handle case with no put options
        # Concatenate the combined calls and puts dataframes
        data = pd.concat([data_calls, data_puts], axis=0, ignore_index=True)
        data["strike_spread"] = (
            ((self.spot_price - data["strike"])) / data["strike"] * 100
        )
        data["mid"] = (data["bid"] + data["ask"]) / 2
        data["expiration_date"] = data["contractSymbol"].apply(parse_expiration_date)
        data["dte"] = data["expiration_date"].apply(calc_dte)
        remapping = {
            "impliedVolatility": "IV",
            "inTheMoney": "ITM",
            "openInterest": "OI",
        }
        drop = ["contractSize", "currency"]
        data.rename(columns=remapping, inplace=True)
        data.drop(columns=drop, inplace=True)
        # Calculate ratios
        data["vol/OI"] = data["volume"] / data["OI"]

        # Calculate the greeks.
        data = data.apply(lambda row: self.apply_american_option(row), axis=1)
        # Calculate the option risk
        data = self.predict_option_risk(data)
        data = data.apply(lambda row: self.apply_delta_risks(row), axis=1)

        return data

    def _create_snapshot(self, df: pd.DataFrame, path: str):
        df.to_csv(path)

    def apply_american_option(self, row: pd.Series):
        S = self.spot_price
        K = float(row["strike"])
        r = float(self.risk_free_rate)
        q = self.dividend_yield
        sigma = float(row["IV"])
        greek_data = self.greeks_calc.calculate_greeks(
            row["type"], S, K, r, sigma, q, row["dte"]
        )
        row["bs_price"] = greek_data["bs_price"]
        row["delta"] = greek_data["delta"]
        row["gamma"] = greek_data["gamma"]
        row["theta"] = greek_data["theta"]
        row["vega"] = greek_data["vega"]
        row["rho"] = greek_data["rho"]
        return row

    def predict_earnings_outcome(self, earnings_date: str):
        date_format = "%Y-%m-%d"
        if not self.objects_set:
            self._set_objects()

        if type(earnings_date) is str:
            earnings_date = dt.datetime.strptime(earnings_date, date_format)

        exp = min(
            d
            for d in self.expiration_dates
            if dt.datetime.strptime(d, date_format) > earnings_date
        )  # .strftime(date_format)
        data = self.get_options_data()
        data = data.loc[data["expiration_date"] == exp]
        # Parse
        calls = data.loc[data["type"] == "call"]
        puts = data.loc[data["type"] == "put"]

        # Locate ATM strikes
        atm_strike = calls.loc[
            (calls["strike"] - self.spot_price).abs().idxmin(), "strike"
        ]
        # Calculate straddle.
        calls_mid = calls.loc[calls["strike"] == atm_strike, "mid"].iloc[0]
        puts_mid = puts.loc[puts["strike"] == atm_strike, "mid"].iloc[0]
        straddle = calls_mid + puts_mid

        expected_move_pct = straddle / self.spot_price
        expected_move = self.spot_price * expected_move_pct
        return {
            "dollar_move": expected_move,
            "percent_move": expected_move_pct,
            "lower_bound": self.spot_price - expected_move,
            "upper_bound": self.spot_price + expected_move,
        }

    def predict_expiration_expected_moves(self):
        if not self.objects_set:
            self._set_objects()

        data = self.get_options_data()
        predict_data = {}

        for exp in self.expiration_dates:
            df_slice = data.loc[data["expiration_date"] == exp, :]
            calls = df_slice[df_slice["type"] == "call"]
            puts = df_slice[df_slice["type"] == "put"]
            # Locate ATM on the calls side (label-based)
            call_idx = (calls["strike"] - self.spot_price).abs().idxmin()
            atm_strike = calls.loc[call_idx, "strike"]
            call_mid = calls.loc[call_idx, "mid"]
            # Try to pull the put at the very same strike
            put_rows = puts[puts["strike"] == atm_strike]
            if not put_rows.empty:
                put_mid = put_rows["mid"].iloc[0]
            else:
                # fallback: find the puts strike closest to spot (positional)
                pos = np.abs(puts["strike"].values - self.spot_price).argmin()
                put_atm = puts["strike"].iloc[pos]
                put_mid = puts["mid"].iloc[pos]
            straddle = call_mid + put_mid
            dte = df_slice["dte"].iloc[0]
            T = max(dte, 0) / 365
            expected_move_pct = straddle / self.spot_price
            expected_move_dollar = self.spot_price * expected_move_pct
            # IV-based move: make sure to use that same atm_strike if it exists
            try:
                iv_atm = calls.loc[calls["strike"] == atm_strike, "IV"].iloc[0]
            except IndexError:
                # if calls didn’t really have that exact strike, pick nearest
                pos = (calls["strike"].values - self.spot_price).abs().argmin()
                iv_atm = calls["IV"].iloc[pos]
            iv_move = self.spot_price * iv_atm * math.sqrt(T)
            predict_data[exp] = {
                "dte": dte,
                "straddle_cost": straddle,
                "expected_move_pct": expected_move_pct,
                "expected_move_dollar": expected_move_dollar,
                "atm_iv": iv_atm,
                "iv_move": iv_move,
            }
        predict_data = pd.DataFrame.from_dict(predict_data, orient="index")
        predict_data.index = pd.to_datetime(predict_data.index)
        predict_data.sort_index(inplace=True)
        predict_data["spot"] = self.spot_price
        predict_data["upper"] = (
            predict_data["spot"] + predict_data["expected_move_dollar"]
        )
        predict_data["lower"] = (
            predict_data["spot"] - predict_data["expected_move_dollar"]
        )
        predict_data["upper_iv"] = predict_data["spot"] + predict_data["iv_move"]
        predict_data["lower_iv"] = predict_data["spot"] - predict_data["iv_move"]
        return predict_data

    def predict_option_risk(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        # Normalize and compute risk sub-scores in one go (vectorized)
        iv_score = df["IV"] / df["IV"].max()
        delta_score = abs(df["delta"])
        gamma_score = df["gamma"] / df["gamma"].max()
        theta_score = -df["theta"] / df["theta"].min()
        vol_oi_score = (df["vol/OI"] < 0.1).astype(float)
        dte_score = (df["dte"] <= 3).astype(float)

        # Calculate final risk score (vectorized)
        risk_score = (
            iv_score * 0.25
            + delta_score * 0.25
            + gamma_score * 0.15
            + theta_score * 0.15
            + vol_oi_score * 0.10
            + dte_score * 0.10
        )

        # Assign risk_score and risk_level in one efficient step
        df = df.assign(
            risk_score=risk_score,
        )

        return df

    def apply_delta_risks(self, row: pd.Series) -> pd.Series:

        if row["ITM"]:
            row["buyer_risk"] = abs(row["delta"] * 0.50 + row["gamma"] * 0.15)
        else:
            row["buyer_risk"] = abs(
                row["delta"] * 0.70 + row["gamma"] * 0.15 + row["theta"] * 0.10
            )
        row["seller_risk"] = 1 - row["buyer_risk"]
        return row

    def apply_candle_risk(self, row: pd.Series):
        pass
