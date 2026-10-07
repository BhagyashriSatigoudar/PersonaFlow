import pandas as pd
import pickle
import os

from sklearn.model_selection import train_test_split

from sklearn.linear_model import LinearRegression

from sklearn.tree import DecisionTreeRegressor

from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# =====================================
# LOAD STUDY DATASET
# =====================================

file_path = (
    "data/study_performance_dataset_1200_records.xlsx"
)

df = pd.read_excel(file_path)

print("Dataset loaded successfully!")

print(
    "Dataset Shape:",
    df.shape
)

print("\nDataset Columns:")

print(
    df.columns.tolist()
)


# =====================================
# INPUT FEATURES AND TARGET
# =====================================

X = df[[
    "Study_Hours",
    "Attendance",
    "Assignments_Completed",
    "Previous_Score",
    "Revision_Hours",
    "Sleep_Hours",
    "Screen_Time"
]]

y = df[
    "Performance_Score"
]


# =====================================
# SPLIT DATA
# =====================================

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.20,

    random_state=42
)


# =====================================
# CREATE MODELS
# =====================================

models = {

    "Linear Regression":
        LinearRegression(),

    "Decision Tree Regressor":
        DecisionTreeRegressor(
            random_state=42
        ),

    "Random Forest Regressor":
        RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
}


# =====================================
# TRAIN AND COMPARE MODELS
# =====================================

best_model = None

best_model_name = ""

best_r2 = -999


for model_name, model in models.items():

    # Train model
    model.fit(
        X_train,
        y_train
    )


    # Prediction
    predictions = model.predict(
        X_test
    )


    # Metrics
    mae = mean_absolute_error(
        y_test,
        predictions
    )


    mse = mean_squared_error(
        y_test,
        predictions
    )


    rmse = mse ** 0.5


    r2 = r2_score(
        y_test,
        predictions
    )


    # Display results

    print("\n----------------------------")

    print(
        model_name
    )

    print(
        "----------------------------"
    )

    print(
        "MAE:",
        round(mae, 2)
    )

    print(
        "RMSE:",
        round(rmse, 2)
    )

    print(
        "R2 Score:",
        round(r2, 4)
    )


    # Select best model

    if r2 > best_r2:

        best_r2 = r2

        best_model = model

        best_model_name = model_name


# =====================================
# BEST MODEL RESULT
# =====================================

print("\n============================")

print(
    "BEST MODEL:",
    best_model_name
)

print(
    "============================"
)

print(
    "R2 Score:",
    round(best_r2, 4)
)


# =====================================
# CREATE MODELS FOLDER
# =====================================

os.makedirs(
    "models",
    exist_ok=True
)


# =====================================
# SAVE BEST MODEL
# =====================================

model_path = (
    "models/study_model.pkl"
)


with open(
    model_path,
    "wb"
) as file:

    pickle.dump(
        best_model,
        file
    )


print(
    "\nModel saved successfully!"
)

print(
    "Saved:",
    model_path
)