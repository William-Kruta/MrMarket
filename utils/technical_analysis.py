import pandas as pd
import pandas_ta as pta


def get_RSI(close: pd.Series, period=14):
    rsi = pta.rsi(close=close, length=period)
    return rsi


def get_SMA(close: pd.Series, period: int) -> pd.Series:
    sma = pta.sma(close, length=period)
    return sma


def get_EMA(close: pd.Series, period: int) -> pd.Series:
    ema = pta.ema(close, length=period)
    return ema


def get_MACD(close: pd.Series, fast_period=12, slow_period=26, signal_period=9):
    macd = pta.macd(close, fast=fast_period, slow=slow_period, signal=signal_period)
    return macd


def get_BBands(close: pd.Series, period: int = 20):
    bb = pta.bbands(close=close, length=period)
    return bb


def get_cross(series1: pd.Series, series2: pd.Series):
    cross = pta.cross(series1, series2)
    return cross
