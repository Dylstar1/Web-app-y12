import yfinance as yf
from datetime import datetime
import pandas as pd
from Prediction import predict_stock_prices  

def get_stock_info(ticker: str):
    if not ticker or len(ticker.strip()) < 1:  
        return None, None, "Please enter a valid ticker symbol"
    
    ticker = ticker.upper().strip()  

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        current_price = None  
        for key in ['currentPrice', 'regularMarketPrice', 'price']:
            if info.get(key):
                current_price = info.get(key)
                break

        growth_5y = 0.0
        try:
            growth_df = stock.growth_estimates
            if isinstance(growth_df, pd.DataFrame) and not growth_df.empty:
                if '+5y' in growth_df.index and 'stock' in growth_df.columns:
                    growth_5y = float(growth_df.loc['+5y', 'stock'])
        except Exception:
            pass

        recent_dividend = 0.0
        try:
            dividends = stock.dividends
            if not dividends.empty:
                recent_dividend = float(dividends.iloc[-1])
        except Exception:
            pass

        hist = stock.history(period="3mo")
        if hist.empty:
            return None, None, f"No market data available for {ticker}."

        stock_data = {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName') or f"{ticker} Stock",
            'current_price': round(current_price, 2) if current_price else round(float(hist['Close'].iloc[-1]), 2),
            'previous_close': round(info.get('regularMarketPreviousClose', 0), 2),
            'summary': info.get('longBusinessSummary', ''),
            'currency': info.get('currency', 'USD'),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'recent_dividend': recent_dividend,
            'dividend_yield_pct': round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0.0
        }

        hist_dates = hist.index.strftime('%Y-%m-%d').tolist()
        close_prices = hist['Close'].tolist()
        volumes = hist['Volume'].tolist()

        pred_dates, pred_prices = predict_stock_prices(
            hist_dates=hist_dates,
            close_prices=close_prices,
            volumes=volumes,
            expected_growth_5y=growth_5y
        )

        chart_data = {
            'dates': hist_dates,
            'close': [round(p, 2) for p in close_prices],
            'pred_dates': pred_dates,
            'pred_prices': pred_prices
        }

        return stock_data, chart_data, None

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None, None, f"Failed to fetch data for {ticker} try again."