import numpy as np  # numerical operations (arrays, math, etc)
import pandas as pd  # working with tables (csv)

# matplotlib inline
import matplotlib.pyplot as plt  # plotting graphs
plt.style.use('ggplot')  # making it look pretty

from sklearn.linear_model import LinearRegression

from sklearn.metrics import mean_absolute_error,mean_squared_error  # mae - average error, mse - square error (penalises large mistakes)

#Import data as a Pandas DataFrame
insects = pd.read_csv('../data/insects.csv', sep='\t')  # read csv file into a dataframe, with tab separations
insects = pd.DataFrame({
    'continent': insects['continent'],
    'latitude': insects['latitude'],
    'sex': insects['sex'],
    'wingsize': insects['wingsize']
})  # creates a dataframe with only selected columns - creating a clean set of relevant data

# Filter the data to only male insects
insects = insects[insects.sex == 1]

# Features variable
X_insects = insects[['wingsize']]  # defines a feature - an input used to make predictions
# Target variable
y_insects = insects['latitude']  # what we want to predict, in this case given wing size, predict the latitude

print(insects.head())  # displays the first 5 rows

#Plot the data
plt.scatter(X_insects, y_insects, label="Actual Data", color='g')
plt.xlabel("Wing size")
plt.ylabel("Latitude")
plt.legend()
plt.show()

# instantiate linear regression object
insects_regression = LinearRegression()  # create and train model

# Fit the model
insects_regression.fit(X_insects, y_insects)  # finds the best straight line -- y = mx + b + error

# Predict the target for the whole dataset
latitude_predictions = insects_regression.predict(X_insects)  # predict latitude for all training data

#Predict the target for a new data point  - creates a new insect with wing size 800
new_insect = pd.DataFrame({
    'wingsize': [800]
})
new_insect['latitude'] = insects_regression.predict(new_insect)  # predict the new insects latitude
print(f"New insect is:\n{new_insect}")

#Plot the predictions compared to the actual data
plt.scatter(X_insects, y_insects, label="Actual Data", color='g')
plt.scatter(X_insects, latitude_predictions, label="Predicted Data", c='r')
plt.xlabel("Wing size")
plt.ylabel("Latitude")
plt.legend()
plt.show()

#Get Evalutative Data from the model
print(f"Model coefficient :{insects_regression.coef_}")  # slope of the line
print(f"Model y intercept :{insects_regression.intercept_}")  # intercept of the line
print(f"Model score :{insects_regression.score(X_insects,y_insects)}")  # This is R² score (coefficient of determination) -- 1 is perfect, 0 is useless
mae = mean_absolute_error(y_true=y_insects,y_pred=latitude_predictions)
mse = mean_squared_error(y_true=y_insects,y_pred=latitude_predictions)
print("MAE:",mae)  # average size of errors
print("MSE:",mse)  # squares the errors

#Optional: Manually Evaluate the loss and cost of the model
model_loss = pd.DataFrame({
    'Target': y_insects,
    'Predicted result': latitude_predictions,
    'Loss': abs(insects_regression.predict(X_insects).round(2) - y_insects)**2
})
model_cost = 1 / (2 * model_loss.shape[0]) * model_loss['Loss'].sum()  # computes cost function

print(f"The cost of this model is {model_cost:.5f}")
print(model_loss)  # prints error table

"""
┌─────────────────────────────┐
│ 1. Load Libraries           │
│ numpy, pandas, matplotlib   │
│ sklearn (ML tools)          │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 2. Load Dataset             │
│ pd.read_csv()               │
│ → insects DataFrame         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 3. Clean & Select Data      │
│ Keep: continent, latitude,  │
│ sex, wingsize               │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 4. Filter Data              │
│ Keep only males (sex == 1)  │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 5. Split Variables          │
│ X = wingsize (input)        │
│ y = latitude (output)       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 6. Visualise Data           │
│ Scatter plot                │
│ (Wing size vs Latitude)     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 7. Create Model             │
│ LinearRegression()          │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 8. Train Model              │
│ fit(X, y)                   │
│ → Finds best line (y=mx+b)  │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 9. Make Predictions         │
│ predict(X)                  │
│ → predicted latitudes       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 10. Predict New Data        │
│ wingsize = 800              │
│ → model predicts latitude   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 11. Visual Comparison       │
│ Green = actual data         │
│ Red = predicted data        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 12. Evaluate Model          │
│ coef_ → slope (m)           │
│ intercept_ → intercept (b)  │
│ score() → R²                │
│ MAE, MSE → error measures   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 13. Manual Cost Calculation │
│ squared error for each row  │
│ → overall model cost        │
└─────────────────────────────┘
"""