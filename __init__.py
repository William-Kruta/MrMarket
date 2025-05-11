import time
from data.options import Options
from config.config import get_snapshot_dir, get_daily_candles_dir, get_statements_dir
from utils.plot import plot_expected_moves, plot_earnings_moves
from data.statements import FinancialStatements


from data.candles import Candles

if __name__ == "__main__":
    ticker = "RKLB"
    start = time.time()
    f = FinancialStatements("AFRM", get_statements_dir(), get_daily_candles_dir())
    data = f.get_growth()

    print(f"Data: {data}")
    # o.predict_expiration_expected_moves()
    # predict_earnings_outcome("2025-05-07")
    # plot_expected_moves(data)
    # plot_earnings_moves(ticker, o.candles, data)
    end = time.time()
    elapse = end - start
    print(f"Elpase: {elapse}")
