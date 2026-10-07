import pandas as pd

# Load the Excel dataset
file_path = "data/financial_forecasting_dataset_1200_records.xlsx"

df = pd.read_excel(file_path)

# Display first 5 records
print(df.head())

# Display dataset information
print("\nDataset Shape:")
print(df.shape)

print("\nColumn Names:")
print(df.columns.tolist())

print("\nDataset Information:")
df.info()