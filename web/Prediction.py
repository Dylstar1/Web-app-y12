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

