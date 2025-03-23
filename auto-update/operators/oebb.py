from .common import OperatorAdapter
import pandas as pd
from .utils import *
from collections import Counter


class OebbAdapter(OperatorAdapter, operator_id="ÖBB"):

    FIND_BOT_TRAINS_IN_GTFS = """
    SELECT BoT.trip_short_name as BoT_trip_name,
        trips.trip_short_name as operator_train_id
    FROM BoT INNER JOIN trips ON trips.trip_short_name = BoT.trip_short_name
    WHERE (BoT.trip_short_name is NULL or instr(BoT.trip_short_name , "NJ") or instr(BoT.trip_short_name , "EN") )
        AND (trips.trip_short_name is NULL or instr(trips.trip_short_name , "NJ") or instr(trips.trip_short_name , "EN"))
    GROUP BY BoT.trip_short_name, trips.trip_short_name 
    ORDER BY BoT.trip_short_name
    """

    FIND_ALL_DEPARTURE_DATES = """
        SELECT DISTINCT calendar_dates.date as date FROM 
        trips INNER JOIN calendar_dates ON trips.service_id = calendar_dates.service_id
        WHERE trip_short_name=:train_id
        ORDER by calendar_dates.date;
    """

    def __init__(self, BoT_dataframe: pd.DataFrame, datasource: str):
        super().__init__(BoT_dataframe, datasource)

    def unique_days_of_week(self, operator_train_id):
        df = execute_query(
            self.db_file, self.FIND_ALL_DEPARTURE_DATES, train_id=operator_train_id
        )
        date_column = "date"

        return unique_days_of_week_summary(df, date_column)

    def find_matching_bot_trains(self):
        matching_trains = execute_query(self.db_file, self.FIND_BOT_TRAINS_IN_GTFS)
        return matching_trains

    def extract_operator_format_train_ids(self, route_short_name):
        trains = extract_first_matching_if_any(route_short_name, r"\b(EN|NJ) \d+\b")
        return trains
