from .common import OperatorAdapter

class OebbAdapter(OperatorAdapter, operator_id="OBB"):

    FIND_BOT_TRAINS_IN_GTFS = """
    SELECT BoT.trip_short_name as BoT_trip_name,
        trips.trip_short_name as OBB_trip_name
    FROM BoT INNER JOIN trips ON trips.trip_short_name = BoT.trip_short_name
    WHERE (BoT.trip_short_name is NULL or instr(BoT.trip_short_name , "NJ") or instr(BoT.trip_short_name , "EN") )
        AND (trips.trip_short_name is NULL or instr(trips.trip_short_name , "NJ") or instr(trips.trip_short_name , "EN"))
    GROUP BY BoT.trip_short_name, trips.trip_short_name 
    ORDER BY BoT.trip_short_name
    """

    pass
    
    #trains_in_this_gtfs = execute_query(db_file, FIND_BOT_TRAINS_IN_GTFS[country])