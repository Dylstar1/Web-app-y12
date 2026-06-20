import os
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import yfinance as yf

TICKER_FILE = "stocks.txt"

def load_tickers_from_file(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("BTC-USD\nSGML\nNVDA\nKO\n")
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def download_bulk_history():
    tickers = load_tickers_from_file(TICKER_FILE)
    if not tickers:
        print("No tickers found.")
        return

    end_date = datetime.today()
    start_date = end_date - relativedelta(months=18)

    print(f"Downloading data for: {', '.join(tickers)}")

    # We download in a single batch, but if you have hundreds of tickers,
    # consider looping through them one by one with a time.sleep() pause.
    raw_data = yf.download(
        tickers=tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        group_by="ticker",
        threads=True,
    )

    all_records = []
    for ticker in tickers:
        # Check if the ticker exists in the returned object
        # yfinance returns a DataFrame with ticker as the first level of columns
        try:
            # Handle the structure where there is only one ticker vs multiple
            if len(tickers) == 1:
                df = raw_data.copy()
            else:
                df = raw_data[ticker].copy()
                
            df = df.dropna(how="all")
            df["Ticker"] = ticker
            all_records.append(df.reset_index())
        except KeyError:
            print(f"Warning: Could not find data for {ticker}")

    if all_records:
        final_df = pd.concat(all_records, ignore_index=True)
        final_df.to_csv("bulk_prices.csv", index=False)
        print("Done! File saved as 'bulk_prices.csv'.")
    else:
        print("No data retrieved.")

if __name__ == "__main__":
    download_bulk_history()
