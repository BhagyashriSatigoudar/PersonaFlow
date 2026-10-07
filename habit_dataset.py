import pandas as pd
import random
import os

# Number of records
NUM_RECORDS = 1200

data = []

for i in range(NUM_RECORDS):

    # Sleep hours per day
    sleep_hours = round(random.uniform(4, 10), 1)

    # Exercise minutes per day
    exercise_minutes = random.randint(0, 120)

    # Screen time in hours
    screen_time = round(random.uniform(1, 12), 1)

    # Number of daily tasks completed
    tasks_completed = random.randint(0, 15)

    # Habit duration in minutes
    habit_duration = random.randint(5, 180)

    # Calculate Habit Consistency Score
    habit_consistency = (
        sleep_hours * 5
        + exercise_minutes * 0.15
        + tasks_completed * 4
        + habit_duration * 0.05
        - screen_time * 4
    )

    # Add small randomness
    habit_consistency += random.uniform(-10, 10)

    # Keep value between 0 and 100
    habit_consistency = max(
        0,
        min(100, round(habit_consistency, 2))
    )

    # Calculate Productivity Score
    productivity_score = (
        sleep_hours * 4
        + exercise_minutes * 0.15
        + tasks_completed * 4
        + habit_duration * 0.05
        + habit_consistency * 0.4
        - screen_time * 3
    )

    # Add randomness
    productivity_score += random.uniform(-8, 8)

    # Keep between 0 and 100
    productivity_score = max(
        0,
        min(100, round(productivity_score, 2))
    )

    data.append([
        sleep_hours,
        exercise_minutes,
        screen_time,
        tasks_completed,
        habit_duration,
        habit_consistency,
        productivity_score
    ])


# Column names
columns = [
    "Sleep_Hours",
    "Exercise_Minutes",
    "Screen_Time",
    "Tasks_Completed",
    "Habit_Duration",
    "Habit_Consistency",
    "Productivity_Score"
]


# Create DataFrame
df = pd.DataFrame(data, columns=columns)


# Create data folder
os.makedirs("data", exist_ok=True)


# Save dataset
file_path = "data/habit_productivity_dataset_1200_records.xlsx"

df.to_excel(
    file_path,
    index=False
)

print("Habit/Productivity dataset created successfully!")
print("Dataset Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nSaved:", file_path)

print("\nFirst 5 Records:")
print(df.head())