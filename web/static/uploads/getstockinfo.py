import yfinance as yf
from datetime import datetime
import pandas as pd

def get_stock_info(ticker: str):
    if not ticker or len(ticker.strip()) < 1:  # if ticker name is too short
        return None, None, "Please enter a valid ticker symbol"
    
    ticker = ticker.upper().strip()  # convert to uppercase, remove any unwanted spaces

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Current price -- get the first price found then exit loop
        current_price = None  # initialise current price
        for key in ['currentPrice', 'regularMarketPrice', 'price']:
            if info.get(key):
                current_price = info.get(key)
                break

        stock_data = {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName') or f"{ticker} Stock",
            'current_price': round(current_price, 2) if current_price else None,
            'previous_close': round(info.get('regularMarketPreviousClose', 0), 2),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency', 'USD'),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M"),
            #'dividends': info.get('dividends'),
            'dividends': stock.dividends
            }

        # Get historical data for chart (last 3 months)
        hist = stock.history(period="1mo")
        chart_data = None

        #vdiv = stock.dividends
        df = pd.DataFrame(stock_data)
        print(df)

        if not hist.empty:
            chart_data = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'close': hist['Close'].round(2).tolist()
            }

        return stock_data, chart_data, None

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None, None, f"Failed to fetch data for {ticker}. Please try again."

get_stock_info(ticker="BHP.ax")