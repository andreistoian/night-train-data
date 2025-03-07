import sqlite3
import zipfile
import os
import pandas as pd
import tempfile

# Set your paths
GTFS_ZIP_FILES = ["data/GTFS_OP_2025_obb.zip", "data/export-ter-gtfs-last.zip"]  # Path to your GTFS zip file

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

def execute_query(db_path, query, **params):
    conn = sqlite3.connect(db_path)

    # Execute query using parameters safely
    df = pd.read_sql_query(query, conn, params=params)

    conn.close()
    return df

def add_bot_table(db_path, data):
    conn = sqlite3.connect(db_path)
    data.to_sql("BoT", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

BoT_data = pd.read_csv("data/B-o-T_nighttrain_DB - trips.csv", dtype=str)
BoT_data.columns = [col.strip().lower() for col in BoT_data.columns]  # Normalize column names

FIND_BOT_TRAINS_IN_GTFS = """
SELECT BoT.trip_short_name as BoT_trip_name,
	trips.trip_short_name as OBB_trip_name
FROM BoT LEFT JOIN trips ON trips.trip_short_name = BoT.trip_short_name
WHERE (BoT.trip_short_name is NULL or instr(BoT.trip_short_name , "NJ") or instr(BoT.trip_short_name , "EN") )
	AND (trips.trip_short_name is NULL or instr(trips.trip_short_name , "NJ") or instr(trips.trip_short_name , "EN"))
	AND (trips.trip_short_name is NOT NULL OR BoT.trip_short_name is not null)
GROUP BY BoT.trip_short_name, trips.trip_short_name 
ORDER BY BoT.trip_short_name
"""

for gtfs_file in GTFS_ZIP_FILES:
    temp_dir = tempfile.mkdtemp(prefix="gtfs_")
    db_dir = tempfile.mkdtemp(prefix="gtfs_")
    db_file = os.path.join(db_dir, "gtfs_database.sqlite")  # SQLite database file
    print(f"Importing {gtfs_file} to {db_file}")

    ensure_dir(db_dir)

    extract_gtfs(gtfs_file, temp_dir)
    import_gtfs_to_sqlite(db_file, temp_dir)

    add_bot_table(db_file, BoT_data)

    trains_in_this_gtfs = execute_query(db_file, FIND_BOT_TRAINS_IN_GTFS)
    print(trains_in_this_gtfs)

    



