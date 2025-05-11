import os
import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt


from utils.dates import is_stale
from utils.utils import handle_growth
from data.candles import Candles


class FinancialStatements:
    def __init__(
        self, ticker: str, cache_dir: str, candle_dir: str, yf_obj: yf.Ticker = None
    ):
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
        self.candle_dir = candle_dir
        self.yf_obj = yf_obj
        self.objects_set = False

        # Path creation
        self.ticker_dir = os.path.join(self.cache_dir, self.ticker)
        os.makedirs(self.ticker_dir, exist_ok=True)
        self.paths = {
            "income_statement": os.path.join(
                self.ticker_dir, "{}_{}_income_statement.csv"
            ),
            "balance_sheet": os.path.join(self.ticker_dir, "{}_{}_balance_sheet.csv"),
            "cash_flow": os.path.join(self.ticker_dir, "{}_{}_cash_flow.csv"),
        }

        self.statements = {}

    def set_objects(self):
        if self.yf_obj is None:
            self.yf_obj = yf.Ticker(self.ticker)

        self.candle_obj = Candles(self.ticker, self.candle_dir)
        self.candles = self.candle_obj.get_candles()
        self.objects_set = True

    def set_statements(self, annual: bool = True):
        if not self.objects_set:
            self.set_objects()

        if annual:
            period = "annual"
            stale_threshold = 400
        else:
            period = "quarter"
            stale_threshold = 100

        for k, v in self.paths.items():
            path = v.format(self.ticker, period)
            df = self._read_file(path)
            # If empty, fetch new data and save it.
            if df.empty:
                df = self._fetch_statements(k, annual)
                df.to_csv(path)
            else:
                cols = df.columns.to_list()
                last_date = cols[-1]
                stale = is_stale(last_date, stale_threshold=stale_threshold)
                if stale:
                    new_df = self._fetch_statements(k, annual)
                    new_date = new_df.columns.to_list()
                    # Get dates that are not in local data.
                    unique_dates = [x for x in new_date if x not in cols]
                    unique_data = new_df[unique_dates]
                    df = pd.concat([df, unique_data], axis=1)
                    df.to_csv(path)

            candle_data = self.create_candle_rows(df.columns.to_list())
            df = pd.concat([df, candle_data], axis=0)
            self.statements[k] = df

    def get_statements(self, annual: bool = True):
        if self.statements == {}:
            self.set_statements(annual)
        return self.statements

    def _read_file(self, path: str):
        try:
            df = pd.read_csv(path)
            cols = df.columns.to_list()
            if "Unnamed: 0" in cols:
                df.rename(columns={"Unnamed: 0": "Index"}, inplace=True)
                df.set_index("Index", inplace=True)

            return df
        except FileNotFoundError:
            return pd.DataFrame

    def _fetch_statements(self, statement_type: str, annual: bool):
        data = None
        if annual:
            if statement_type == "income_statement":
                data = self.yf_obj.income_stmt
            elif statement_type == "balance_sheet":
                data = self.yf_obj.balance_sheet
            elif statement_type == "cash_flow":
                data = self.yf_obj.cash_flow
        else:
            if statement_type == "income_statement":
                data = self.yf_obj.quarterly_income_stmt
            elif statement_type == "balance_sheet":
                data = self.yf_obj.quarterly_balance_sheet
            elif statement_type == "cash_flow":
                data = self.yf_obj.quarterly_cash_flow
        data = data.iloc[:, ::-1]
        return data

    def create_candle_rows(self, dates: list):
        if not self.objects_set:
            self.set_objects()
        index = 0
        high, low, average = [], [], []
        print(f"Candles: {self.candles}")
        for d in dates:
            if index == 0:
                _high = np.nan
                _low = np.nan
                _average = np.nan
            else:
                prev_date = dates[index - 1]
                candle_slice = self.candles.loc[prev_date:d]
                _high = candle_slice["High"].max()
                _low = candle_slice["Low"].min()
                _average = candle_slice["Close"].mean()

            print(f"High: {_high}")
            high.append(_high)
            low.append(_low)
            average.append(_average)
            index += 1

        df_data = {"high": high, "low": low, "average": average}

        df = pd.DataFrame(df_data, index=dates)  # ["high", "low", "average"])
        return df.T

    def get_ratios(self, annual: bool = True):
        if self.statements == {}:
            self.set_financial_statements(annual)

        ratios = pd.DataFrame()

    def get_margins(self, annual: bool = True, return_percent: bool = True):
        if self.statements == {}:
            self.set_statements(annual)
        margins = pd.DataFrame()

        if return_percent:
            multiplier = 100
        else:
            multiplier = 1
        revenue = self.statements["income_statement"].loc["Total Revenue"]
        margins["gross_margin"] = (
            self.statements["income_statement"].loc["Gross Profit"]
            / revenue
            * multiplier
        )
        margins["operating_margin"] = (
            self.statements["income_statement"].loc["Operating Income"]
            / revenue
            * multiplier
        )
        margins["profit_margin"] = (
            (self.statements["income_statement"].loc["Net Income"])
            / revenue
            * multiplier
        )
        margins["fcf_margin"] = (
            self.statements["cash_flow"].loc["Free Cash Flow"] / revenue * 100
        )
        return margins.T

    def get_growth(self, annual: bool = True, return_percent: bool = True):
        if self.statements == {}:
            self.set_statements(annual)

        growth = pd.DataFrame()

        growth["revenue"] = handle_growth(
            self.statements["income_statement"].loc["Total Revenue"]
        )
        growth["earnings"] = handle_growth(
            self.statements["income_statement"].loc["Net Income"]
        )
        growth["eps"] = handle_growth(
            self.statements["income_statement"].loc["Basic EPS"]
        )

        growth.index = self.statements["income_statement"].columns
        return growth.T

    def breakdown_operating_expenses(
        self, annual: bool = True, return_percent: bool = True
    ) -> pd.DataFrame:
        if self.statements == {}:
            self.set_statements(annual)
        revenue = self.statements["income_statement"].loc["Total Revenue"]
        expense_breakdown = pd.DataFrame()

        if return_percent:
            multiplier = 100
        else:
            multiplier = 1
        try:
            expense_breakdown["R&D"] = (
                self.statements["income_statement"].loc["Research And Development"]
                / revenue
                * multiplier
            )
        except KeyError:
            expense_breakdown["R&D"] = np.nan
        expense_breakdown["SG&A"] = (
            self.statements["income_statement"].loc[
                "Selling General And Administration"
            ]
            / revenue
            * multiplier
        )
        expense_breakdown["S&M"] = (
            self.statements["income_statement"].loc["Selling And Marketing Expense"]
            / revenue
            * multiplier
        )
        expense_breakdown["G&A"] = (
            self.statements["income_statement"].loc[
                "General And Administrative Expense"
            ]
            / revenue
            * multiplier
        )

        return expense_breakdown.T
