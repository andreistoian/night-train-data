import os
import pandas as pd
import tempfile

import operators as C

# Set your paths
SCHEDULE_FILES = {
    #    "UK": "data/ukraine.csv",
    #    "MAV": "data/gtfsMavMenetrend.zip",
    #    "SJ": "data/sweden-20250307.zip",
    #    "PKP": "data/pkpic.zip",
    #    "CFR": "data/sntfc-cfr-calatori-s.a_1303-tr_2025.xml",
    "SNCF": "data/export-intercites-gtfs-last.zip",
    #    "OBB": "data/GTFS_OP_2025_obb.zip",
}  # Path to your GTFS zip file

sheet_names = ["agencies", "routes", "stops", "trips", "trip_stop"]
BoT_data = {}
for sn in sheet_names:
    BoT_data[sn] = pd.read_excel(
        "data/Local_B-o-T_nighttrain_DB.xlsx", dtype=str, sheet_name=sn
    )
    BoT_data[sn].columns = [
        col.strip().lower() for col in BoT_data[sn].columns
    ]  # Normalize column names

for operator, schedule_file in SCHEDULE_FILES.items():
    country_adapter_cls = C.OPERATOR_ADAPTERS[operator]
    adapter = country_adapter_cls(BoT_data["trips"], schedule_file)
    trains = adapter.find_matching_bot_trains()

    BoT_data_routes_for_agency = BoT_data["routes"][
        BoT_data["routes"]["agency_id"].str.contains(operator, case=False, na=False)
    ]
    for route_id in BoT_data_routes_for_agency["route_short_name"].values:
        parts = route_id.split("=")
        trains_to_check = list(map(lambda s: s.strip(), parts))

        for train_id in trains["operator_train_id"].values:
            if train_id in trains_to_check:
                continue
            print(train_id)
            print(adapter.unique_days_of_week(train_id))
            pass
