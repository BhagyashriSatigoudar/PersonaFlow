import pandas as pd
import numpy as np
import os

# =====================================
# STUDY PERFORMANCE DATASET GENERATOR
# =====================================

np.random.seed(42)

# Number of records
num_records = 1200


# =====================================
# GENERATE STUDY FEATURES
# =====================================

study_hours = np.round(
    np.random.uniform(1, 12, num_records),
    1
)

attendance = np.round(
    np.random.uniform(40, 100, num_records),
    2
)

assignments_completed = np.random.randint(
    0, 11, num_records
)

previous_score = np.round(
    np.random.uniform(30, 100, num_records),
    2
)

revision_hours = np.round(
    np.random.uniform(0, 6, num_records),
    1
)

sleep_hours = np.round(
    np.random.uniform(4, 10, num_records),
    1
)

screen_time = np.round(
    np.random.uniform(1, 10, num_records),
    1
)


# =====================================
# GENERATE STUDY PERFORMANCE SCORE
# =====================================

performance_score = (
    study_hours * 4
    + attendance * 0.20
    + assignments_completed * 2
    + previous_score * 0.25
    + revision_hours * 3
    + sleep_hours * 1.5
    - screen_time * 1.5
    + np.random.normal(0, 5, num_records)
)


# Keep score between 0 and 100

performance_score = np.clip(
    performance_score,
    0,
    100
)

performance_score = np.round(
    performance_score,
    2
)


# =====================================
# CREATE DATAFRAME
# =====================================

df = pd.DataFrame({

    "Study_Hours": study_hours,

    "Attendance": attendance,

    "Assignments_Completed": assignments_completed,

    "Previous_Score": previous_score,

    "Revision_Hours": revision_hours,

    "Sleep_Hours": sleep_hours,

    "Screen_Time": screen_time,

    "Performance_Score": performance_score

})


# =====================================
# CREATE DATA FOLDER
# =====================================

os.makedirs(
    "data",
    exist_ok=True
)


# =====================================
# SAVE DATASET
# =====================================

file_path = (
    "data/study_performance_dataset_1200_records.xlsx"
)


df.to_excel(
    file_path,
    index=False
)


# =====================================
# DISPLAY RESULT
# =====================================

print(
    "Study Performance dataset created successfully!"
)

print(
    "Dataset Shape:",
    df.shape
)

print(
    "Saved:",
    file_path
)

print(
    "\nFirst 5 Records:"
)

print(
    df.head()
)