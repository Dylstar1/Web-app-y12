import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge, LinearRegression

def predict_stock_prices(hist_dates, close_prices, volumes, expected_growth_5y=0.0, degree=2, days_to_predict=7):
    if len(close_prices) < degree + 1:
        return [], []

    mean_volume = np.mean(volumes) if np.mean(volumes) > 0 else 1
    scaled_volume = np.array(volumes) / mean_volume

    X_train = pd.DataFrame({
        'day_index': np.arange(len(close_prices)),
        'volume_feature': scaled_volume,
        'growth_feature': np.full(len(close_prices), expected_growth_5y if expected_growth_5y is not None else 0.0)
    })
    y_train = np.array(close_prices)

    use_ridge = True               
    ridge_alpha = 1.5              
    weight_day = 1.0               
    weight_volume = 0.15           
    weight_growth = 0.50           

    X_train_w = X_train.copy()
    X_train_w['day_index'] = X_train_w['day_index'] * weight_day
    X_train_w['volume_feature'] = X_train_w['volume_feature'] * weight_volume
    X_train_w['growth_feature'] = X_train_w['growth_feature'] * weight_growth

    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_train_poly = poly.fit_transform(X_train_w)

    model = Ridge(alpha=ridge_alpha) if use_ridge else LinearRegression()
    model.fit(X_train_poly, y_train)

    future_days = np.arange(len(close_prices), len(close_prices) + days_to_predict)
    X_future = pd.DataFrame({
        'day_index': future_days,
        'volume_feature': np.ones(days_to_predict),
        'growth_feature': np.full(days_to_predict, expected_growth_5y if expected_growth_5y is not None else 0.0)
    })

    X_future_w = X_future.copy()
    X_future_w['day_index'] = X_future_w['day_index'] * weight_day
    X_future_w['volume_feature'] = X_future_w['volume_feature'] * weight_volume
    X_future_w['growth_feature'] = X_future_w['growth_feature'] * weight_growth

    X_future_poly = poly.transform(X_future_w)
    y_future_pred = model.predict(X_future_poly).round(2).tolist()

    last_date = datetime.strptime(hist_dates[-1], '%Y-%m-%d')
    pred_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, days_to_predict + 1)]

    return pred_dates, y_future_pred

if __name__ == "__main__":
    import yfinance as yf
    import matplotlib.pyplot as plt
    
    plt.style.use('ggplot')

    user_selection = input("Enter ticker symbol: ")
    test_ticker = user_selection.upper().strip() or "AAPL"
    
    print(f"Fetching yfinance data for: {test_ticker}...")
    stock = yf.Ticker(test_ticker)
    hist = stock.history(period="3mo")
    
    if hist.empty:
        print(f"Could not find market data for '{test_ticker}'")
    else:
        full_dates = hist.index.strftime('%Y-%m-%d').tolist()
        full_prices = hist['Close'].tolist()
        full_volumes = hist['Volume'].tolist()

        growth_5y = 0.0
        try:
            growth_df = stock.growth_estimates
            if '+5y' in growth_df.index:
                growth_5y = float(growth_df.loc['+5y', 'stock'])
        except Exception:
            pass

        days_to_predict = 7
        split_index = len(full_prices) - 20 - days_to_predict

        train_dates = full_dates[:split_index]
        train_prices = full_prices[:split_index]
        train_volumes = full_volumes[:split_index]

        actual_dates = full_dates[split_index : split_index + days_to_predict]
        actual_prices = full_prices[split_index : split_index + days_to_predict]

        pred_dates, pred_prices = predict_stock_prices(
            train_dates, 
            train_prices, 
            train_volumes, 
            growth_5y, 
            days_to_predict=days_to_predict
        )

        plt.figure(figsize=(10, 5.5))
        
        finalHistDate = train_dates[-1]
        finalHistPrice = train_prices[-1]
        
        plt.plot(train_dates[-30:], train_prices[-30:], 
                 label="Stock History", 
                 color="#348ABD", 
                 linewidth=3, 
                 linestyle="-")
        
        plt.plot([finalHistDate] + pred_dates, [finalHistPrice] + pred_prices, 
                 label="Predicted Data", 
                 color="#E24A33", 
                 linewidth=3, 
                 linestyle="-.", 
                 marker="s", 
                 markersize=6)
        
        plt.title(f"{test_ticker} Prices Test", fontsize=14, fontweight='bold', pad=15)
        plt.xlabel("Date", fontsize=11, labelpad=10)
        plt.ylabel("Price", fontsize=11, labelpad=10)
        
        plt.gca().xaxis.set_major_locator(plt.MaxNLocator(nbins=8)) 
        plt.xticks(rotation=45)
        
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=True, facecolor='#ffffff')
        
        plt.tight_layout()
        plt.show()