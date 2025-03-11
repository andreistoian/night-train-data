import sqlite3
import zipfile
import os
import pandas as pd
import tempfile
from datetime import timedelta
import time
import re

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

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
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
            df.columns = [col.strip().lower() for col in df.columns]  # Normalize column names

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