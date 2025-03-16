import pandas as pd

from .common import OperatorAdapter
from .utils import *
from collections import Counter


class SncfAdapter(OperatorAdapter, operator_id="SNCF"):
    FIND_BOT_TRAINS_IN_GTFS = """
    SELECT BoT.trip_short_name as BoT_trip_name,
        trips.trip_headsign as operator_train_id
    FROM BoT LEFT JOIN trips ON trips.trip_headsign = replace(BoT.trip_short_name, "IC Nuit ", "")
    WHERE (BoT.trip_short_name is NULL or instr(BoT.trip_short_name , "IC Nuit") )
        AND (trips.trip_headsign is NOT NULL OR BoT.trip_short_name is not null)
    GROUP BY BoT.trip_short_name, trips.route_id
    ORDER BY BoT.trip_short_name
    """

    FIND_UNIQUE_DEPARTURES_PER_TRAIN = """SELECT 
            departure_time, 
            group_concat(calendar_dates.date, ' ') as all_dates_with_same_departure 
        FROM 
	        trips 
                INNER JOIN calendar_dates ON trips.service_id = calendar_dates.service_id
	            INNER JOIN stop_times on stop_times.trip_id = trips.trip_id
        WHERE trip_headsign=:train_id  AND stop_sequence = 0
        GROUP BY departure_time
        ORDER by calendar_dates.date;
    """

    CHECK_TRAIN_ALWAYS_HAS_SAME_NUMBER_OF_STOPS = """SELECT DISTINCT MAX(stop_sequence) FROM 
        trips INNER JOIN calendar_dates ON trips.service_id = calendar_dates.service_id
        INNER JOIN stop_times on stop_times.trip_id = trips.trip_id
    WHERE trip_headsign=:train_id 
    GROUP by stop_times.trip_id
    ORDER by calendar_dates.date;"""

    FIND_UNIQUE_ARRIVALS_PER_TRAIN = """
    SELECT arrival_time FROM trips INNER JOIN stop_times on stop_times.trip_id = trips.trip_id 
    WHERE stop_sequence = (
        SELECT DISTINCT MAX(stop_sequence) FROM 
            trips INNER JOIN calendar_dates ON trips.service_id = calendar_dates.service_id
            INNER JOIN stop_times on stop_times.trip_id = trips.trip_id
        WHERE trip_headsign=:train_id 
        GROUP by stop_times.trip_id)
    AND trip_headsign=:train_id"""

    FIND_ALL_DEPARTURE_DATES = """
        SELECT calendar_dates.date as date FROM 
        trips INNER JOIN calendar_dates ON trips.service_id = calendar_dates.service_id
        WHERE trip_headsign=:train_id
        ORDER by calendar_dates.date;
    """

    def __init__(self, BoT_dataframe: pd.DataFrame, datasource: str):
        super().__init__(BoT_dataframe, datasource)

    def find_matching_bot_trains(self):
        matching_trains = execute_query(self.db_file, self.FIND_BOT_TRAINS_IN_GTFS)
        return matching_trains

    def unique_days_of_week(self, operator_train_id):
        df = execute_query(
            self.db_file, self.FIND_ALL_DEPARTURE_DATES, train_id=operator_train_id
        )
        date_column = "date"

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
        most_common_pattern, count = pattern_counts.most_common(1)[0]

        # Check if the most common pattern is the only pattern
        if count < len(patterns):
            most_common_pattern = f"Usually {most_common_pattern}"

        return week_results, most_common_pattern

    def get_train_timetable(self, operator_train_id):
        departures = execute_query(
            self.db_file, self.FIND_UNIQUE_DEPARTURES_PER_TRAIN, train_id=train_id
        )
        for row in departures.iterrows():
            pass
