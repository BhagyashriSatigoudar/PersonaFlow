import pandas as pd
import pickle
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =====================================
# 1. LOAD DATASET
# =====================================

df = pd.read_excel(
    "data/financial_forecasting_dataset_1200_records.xlsx"
)
df["Category"] = df["Category"].astype(str).str.strip()

print("\nAvailable Categories:")
print(df["Category"].unique())

print("Dataset loaded successfully!")
print("Dataset Shape:", df.shape)


# =====================================
# 2. PREPARE DATE FEATURES
# =====================================

df["Date"] = pd.to_datetime(df["Date"])

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Day"] = df["Date"].dt.day
df["DayOfWeek"] = df["Date"].dt.dayofweek


# =====================================
# 3. ENCODE CATEGORY
# =====================================

label_encoder = LabelEncoder()

df["Category_Encoded"] = label_encoder.fit_transform(
    df["Category"]
)


# =====================================
# 4. SELECT INPUT FEATURES
# =====================================

features = [
    "Income",
    "Budget",
    "Transaction_Count",
    "Category_Encoded",
    "Year",
    "Month",
    "Day",
    "DayOfWeek"
]

X = df[features]


# =====================================
# 5. SELECT TARGET
# =====================================

y = df["Expense"]


# =====================================
# 6. SPLIT DATA
# =====================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# =====================================
# 7. TRAIN BEST MODEL
# =====================================

model = LinearRegression()

model.fit(
    X_train,
    y_train
)


# =====================================
# 8. EVALUATE MODEL
# =====================================

prediction = model.predict(
    X_test
)

mae = mean_absolute_error(
    y_test,
    prediction
)

rmse = mean_squared_error(
    y_test,
    prediction
) ** 0.5

r2 = r2_score(
    y_test,
    prediction
)

print("\n============================")
print("BEST MODEL: Linear Regression")
print("============================")

print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 4))


# =====================================
# 9. CREATE MODELS FOLDER
# =====================================

os.makedirs(
    "models",
    exist_ok=True
)


# =====================================
# 10. SAVE TRAINED MODEL
# =====================================

with open(
    "models/finance_model.pkl",
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


# =====================================
# 11. SAVE CATEGORY ENCODER
# =====================================

with open(
    "models/category_encoder.pkl",
    "wb"
) as file:

    pickle.dump(
        label_encoder,
        file
    )


print("\nModel saved successfully!")
print("Saved: models/finance_model.pkl")

print("Category encoder saved successfully!")
print("Saved: models/category_encoder.pkl")