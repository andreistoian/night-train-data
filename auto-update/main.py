import os
import pandas as pd
import tempfile

import operators as C

# Set your paths
SCHEDULE_FILES = {
    "UK": "data/ukraine.csv",
    "MAV": "data/gtfsMavMenetrend.zip",    
    "SJ": "data/sweden-20250307.zip",
    "PKP": "data/pkpic.zip",
    "CFR": "data/sntfc-cfr-calatori-s.a_1303-tr_2025.xml", 
    "SNCF": "data/export-intercites-gtfs-last.zip", 
    "OBB": "data/GTFS_OP_2025_obb.zip",
}  # Path to your GTFS zip file


BoT_data = pd.read_csv("data/B-o-T_nighttrain_DB - trips.csv", dtype=str)
BoT_data.columns = [col.strip().lower() for col in BoT_data.columns]  # Normalize column names

for operator, schedule_file in SCHEDULE_FILES.items():
    country_adapter_cls = C.OPERATOR_ADAPTERS[operator]
    adapter = country_adapter_cls(BoT_data, schedule_file)
    



