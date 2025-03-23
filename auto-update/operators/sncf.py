import pandas as pd

from .common import OperatorAdapter
from .utils import *


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

        return unique_days_of_week_summary(df, date_column)

    def get_train_timetable(self, operator_train_id):
        departures = execute_query(
            self.db_file, self.FIND_UNIQUE_DEPARTURES_PER_TRAIN, train_id=train_id
        )
        for row in departures.iterrows():
            pass

    def extract_operator_format_train_ids(self, route_short_name):
        trains = extract_first_matching_if_any(route_short_name)
        return trains
