import numpy as np
import pandas as pd

# matplotlib inline
import matplotlib.pyplot as plt
plt.style.use('ggplot')

from sklearn.linear_model import LogisticRegression

from sklearn.metrics import mean_absolute_error,mean_squared_error

#Import data as a Pandas DataFrame
grades = pd.read_csv('student-mat.csv', sep=';')
grades = pd.DataFrame({
    'G1': grades['G1'],
    'G3': grades['G3']
})

# Features variable
X_grades = grades[['G1']]
# Target variable
y_grades = grades['G3']

print(grades.head())

# Plot the data, colour coded by G1
ax = plt.scatter(grades.G1, grades.G3, c=grades['G1'])
plt.xlabel("G1")
plt.ylabel("G3")
plt.colorbar()
plt.show()

# Instantiate a LogisticRegression Object
grades_regression = LogisticRegression(max_iter=5000)
# Fit the model
grades_regression.fit(X_grades, y_grades)

# Predict the target for the whole dataset
grades_predictions = grades_regression.predict(X_grades)

#Predict the target for a new data point
new_student = pd.DataFrame({
    'G1': [10]
})
new_student['G3'] = grades_regression.predict(new_student)
print(f"New student is:\n{new_student}")

#Predict the probabilities for the whole dataset
grades_probabilities = grades_regression.predict_proba(X_grades)

#Predict the probabilities for a new data point
new_student = pd.DataFrame({
    'G1': [10]
})
new_student_probabilities = grades_regression.predict_proba(new_student)
print(f"Probabilities for new student are:\n{new_student_probabilities}")

#Plot the predictions compared to the actual data
fig, axs = plt.subplots(1, 3, figsize=(14, 5))

axs[0].scatter(grades.G1, grades.G3, s=40, c=grades['G1'])
axs[0].set_title("Actual Data")
axs[0].set_xlabel("G1")
axs[0].set_ylabel("G3")

axs[1].scatter(grades.G1, grades_probabilities[:, 1], s=40, c=grades['G1'])
axs[1].set_title("Prediction Probabilities")
axs[1].set_xlabel("G1")
axs[1].set_ylabel("G3 Probability")

axs[2].scatter(grades.G1, grades_predictions, s=40, c=grades['G1'])
axs[2].set_title("Predicted Data")
axs[2].set_xlabel("G1")
axs[2].set_ylabel("G3 Prediction")

plt.show()

# Evaluate the model
mae = mean_absolute_error(y_true=y_grades,y_pred=grades_probabilities[:, 1])
mse = mean_squared_error(y_true=y_grades,y_pred=grades_probabilities[:, 1])
print("MAE:",mae)
print("MSE:",mse)

#Optional: Manually Evaluate the loss and cost of the model
model_loss = pd.DataFrame({
    'Target': y_grades,
    'Predicted result': grades_probabilities[:, 1],
    'Loss': abs(grades_regression.predict(X_grades).round(2) - y_grades)**2
})
model_loss["Predicted result"] = model_loss["Predicted result"].round(0)
model_loss["Loss"] = model_loss["Loss"].abs()
model_cost = 1 / (2 * model_loss.shape[0]) * model_loss['Loss'].sum()

print(f"The cost of this model is  {model_cost:.5f}")
print(f"The model predicted incorrectly {model_loss['Loss'].sum()} times out of {model_loss.shape[0]} predictions")
print(model_loss)
