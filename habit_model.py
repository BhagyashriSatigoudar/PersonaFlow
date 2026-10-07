import pandas as pd
import pickle
import os

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =====================================
# LOAD DATASET
# =====================================

df = pd.read_excel(
    "data/habit_productivity_dataset_1200_records.xlsx"
)

print("Dataset loaded successfully!")
print("Dataset Shape:", df.shape)

print("\nDataset Columns:")
print(df.columns.tolist())


# =====================================
# FEATURES AND TARGET
# =====================================

X = df[
    [
        "Sleep_Hours",
        "Exercise_Minutes",
        "Screen_Time",
        "Tasks_Completed",
        "Habit_Duration",
        "Habit_Consistency"
    ]
]

# Target: Predict Productivity Score
y = df["Productivity_Score"]


# =====================================
# TRAIN / TEST SPLIT
# =====================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# =====================================
# DEFINE MODELS
# =====================================

models = {

    "Linear Regression": LinearRegression(),

    "Decision Tree Regressor": DecisionTreeRegressor(
        random_state=42
    ),

    "Random Forest Regressor": RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )
}


# =====================================
# TRAIN AND EVALUATE MODELS
# =====================================

best_model = None
best_model_name = None
best_r2 = -999


for name, model in models.items():

    print("\n----------------------------")
    print(name)
    print("----------------------------")

    # Train model
    model.fit(X_train, y_train)

    # Prediction
    predictions = model.predict(X_test)

    # Evaluation metrics
    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = mean_squared_error(
        y_test,
        predictions
    ) ** 0.5

    r2 = r2_score(
        y_test,
        predictions
    )

    print("MAE:", round(mae, 2))
    print("RMSE:", round(rmse, 2))
    print("R2 Score:", round(r2, 4))

    # Select best model
    if r2 > best_r2:

        best_r2 = r2
        best_model = model
        best_model_name = name


# =====================================
# SAVE BEST MODEL
# =====================================

os.makedirs(
    "models",
    exist_ok=True
)

with open(
    "models/habit_model.pkl",
    "wb"
) as file:

    pickle.dump(
        best_model,
        file
    )


# =====================================
# FINAL RESULT
# =====================================

print("\n============================")
print("BEST MODEL:", best_model_name)
print("============================")

print("R2 Score:", round(best_r2, 4))

print("\nModel saved successfully!")
print("Saved: models/habit_model.pkl")