import sqlite3
import zipfile
import os
import pandas as pd
import tempfile
from datetime import timedelta
import time
import re

from collections import Counter


def execute_query(db_path, query, **params):
    conn = sqlite3.connect(db_path)

    # Execute query using parameters safely
    df = pd.read_sql_query(query, conn, params=params)

    conn.close()
    return df


def ensure_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


# Step 1: Extract GTFS ZIP Archive
def extract_gtfs(zip_path, extract_to):
    ensure_dir(extract_to)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted GTFS data to: {extract_to}")


# Step 2: Import CSV Files into SQLite
def import_gtfs_to_sqlite(db_path, data_folder):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for file in os.listdir(data_folder):
        if file.endswith(".txt"):  # GTFS uses .txt files (CSV format)
            table_name = file.replace(".txt", "")
            file_path = os.path.join(data_folder, file)

            # Load CSV into a Pandas DataFrame
            df = pd.read_csv(file_path, dtype=str)  # Keep all data as text
            df.columns = [
                col.strip().lower() for col in df.columns
            ]  # Normalize column names

            # Write DataFrame to SQLite
            df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


def convert_seconds_to_time(seconds):
    """Converts seconds since start of the day to HH:MM:SS format."""
    return str(timedelta(seconds=int(seconds)))


def add_bot_table(db_path, data):
    conn = sqlite3.connect(db_path)
    data.to_sql("BoT", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def unique_days_of_week_summary(df, date_column):
    df[date_column] = pd.to_datetime(df[date_column], format="%Y%m%d")
    # Extract the month and day of the week (Monday=0, Sunday=6)
    # Extract the month, week, and day of the week (Monday=0, Sunday=6)
    # Extract the week start date, week end date, and day of the week (Monday=0, Sunday=6)
    df["week_start"] = df[date_column] - pd.to_timedelta(
        df[date_column].dt.dayofweek, unit="d"
    )
    df["week_end"] = df["week_start"] + pd.to_timedelta(6, unit="d")
    df["day_of_week"] = df[date_column].dt.dayofweek

    # Map the day of the week numbers to day names
    day_mapping = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }
    df["day_name"] = df["day_of_week"].map(day_mapping)

    # Define the full set of days of the week
    all_days = set(day_mapping.values())

    # Group by week start date and get unique days of the week for each week
    unique_days_per_week = df.groupby("week_start")["day_name"].unique()

    # Create the result dictionary for each week
    week_results = {}
    for week_start, days in unique_days_per_week.items():
        week_end = week_start + pd.to_timedelta(6, unit="d")
        unique_days = set(days)
        missing_days = all_days - unique_days

        if len(missing_days) == 0:
            pattern = "Every day"
        elif len(missing_days) <= 2:
            sorted_missing_days = sorted(
                missing_days,
                key=lambda day: list(day_mapping.keys())[
                    list(day_mapping.values()).index(day)
                ],
            )
            pattern = f"Every day except {', '.join(sorted_missing_days)}"
        else:
            sorted_days = sorted(
                unique_days,
                key=lambda day: list(day_mapping.keys())[
                    list(day_mapping.values()).index(day)
                ],
            )
            pattern = ", ".join(sorted_days)

        week_results[week_start.strftime("%Y-%m-%d")] = {
            "week_start": week_start.date().strftime("%Y-%m-%d"),
            "week_end": week_end.date().strftime("%Y-%m-%d"),
            "pattern": pattern,
        }

    # Determine the most common pattern for each week
    patterns = [info["pattern"] for info in week_results.values()]
    pattern_counts = Counter(patterns)

    if len(patterns) == 0:
        return {}, "Not scheduled"

    most_common_pat = pattern_counts.most_common(2)
    most_common_pattern, count = most_common_pat[0]

    # Check if the most common pattern is the only pattern
    if count < len(patterns):
        most_common_pattern = f"Usually {most_common_pattern}"

    return week_results, most_common_pattern


def extract_first_matching_if_any(s, pattern=r"\d+\D?"):
    # Search for the pattern in the string
    match = re.search(pattern, s)

    if match:
        # Extract the number part from the match
        return match.group(0)
    else:
        return s
