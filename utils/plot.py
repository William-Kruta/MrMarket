import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import mplfinance as mpf


def plot_expected_moves(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the spot price
    ax.plot(df.index, df["spot"], label="Spot Price")

    # Shade between straddle-based bounds
    ax.fill_between(
        df.index,
        df["lower"],
        df["upper"],
        alpha=0.3,
        label="Straddle-based Range",
        color="blue",
    )

    # Shade between IV-based bounds
    ax.fill_between(
        df.index,
        df["lower_iv"],
        df["upper_iv"],
        alpha=0.2,
        label="IV-based Range",
        color="red",
    )

    # Labels and title
    ax.set_xlabel("Expiry Date")
    ax.set_ylabel("Price")
    ax.set_title("Expected Price Ranges by Expiry")
    ax.legend()
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.show()


def plot_earnings_moves(candles: pd.DataFrame, move_data: dict):
    candles.index = pd.to_datetime(candles.index)
    candles = candles.iloc[-30:]

    last_date = candles.index[-1]
    next_date = last_date + pd.Timedelta(days=1)

    last_close = candles["Close"].iloc[-1]

    # X and Y for cone
    x = [last_date, next_date]
    y_lower = [last_close, move_data["lower_bound"]]
    y_upper = [last_close, move_data["upper_bound"]]

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot Close price
    ax.plot(candles.index, candles["Close"], label="Close", color="blue")

    # Plot cone
    ax.fill_between(
        x, y_lower, y_upper, color="orange", alpha=0.3, label="Expected Move"
    )

    # Extend x-axis
    ax.set_xlim(candles.index[0], next_date + pd.Timedelta(days=1))

    ax.set_title("Stock Close Price and Expected Move Cone")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()

    plt.show()
