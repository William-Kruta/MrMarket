import os
import pandas as pd
import yfinance as yf
import datetime as dt


class YahooNews:
    def __init__(self, ticker: str, cache_dir: str, yf_obj: yf.Ticker = None):
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.ticker_dir = os.path.join(self.cache_dir, self.ticker)
        os.makedirs(self.ticker_dir, exist_ok=True)
        self.yf_obj = yf_obj
        self.objects_set = False

    def set_objects(self):
        if self.yf_obj is None:
            self.yf_obj = yf.Ticker(self.ticker)
        self.objects_set = True

    def get_news(self, export: bool = True):
        file_name = f"{self.ticker}_news_{dt.datetime.now().date()}.csv"
        path = os.path.join(self.ticker_dir, file_name)
        if not os.path.exists(path):
            if not self.objects_set:
                self.set_objects()

            news = self.yf_obj.news
            data = []
            for n in news:
                content = n["content"]
                d = {
                    "type": content["contentType"],
                    "title": content["title"],
                    "summary": content["summary"],
                    "url": content["thumbnail"]["originalUrl"],
                }
                data.append(d)
            df = pd.DataFrame(data)
            if export:
                df.to_csv(path, index=False)
        else:
            df = self.read_news(path)
        return df

    def read_news(self, path: str):
        df = pd.read_csv(path)
        return df
