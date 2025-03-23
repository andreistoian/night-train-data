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
    # "CFR": "data/cfr_cfm_astra_gtfs.zip",
    # "SNCF": "data/export-intercites-gtfs-last.zip",
    "ÖBB": "data/GTFS_OP_2025_obb.zip",
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
    for route_id in BoT_data_routes_for_agency["route_id"].values:
        parts = route_id.split("=")
        trips_for_route = BoT_data["trips"][BoT_data["trips"]["route_id"] == route_id]
        trains_to_check = list(
            map(
                lambda s: adapter.extract_operator_format_train_ids(s.strip()),
                trips_for_route["trip_id"].tolist(),
            )
        )

        for row_idx, train_row in trains.iterrows():
            train_id = train_row["operator_train_id"]
            if train_id is None:
                continue
            # print(train_id)
            if train_id in trains_to_check:
                print(train_id)

                trip_id = BoT_data["trips"]["trip_short_name"].str.contains(
                    train_id, case=False, na=False
                )
                trip_for_route_train = BoT_data["trips"][trip_id]
                if not trip_for_route_train.empty:
                    schedule_type = trip_for_route_train["service_id"].values[0]
                    print("Current BoT schedule: ", schedule_type)

                print(
                    "Schedule from 2025 GTFS:", adapter.unique_days_of_week(train_id)[1]
                )
                print("")
