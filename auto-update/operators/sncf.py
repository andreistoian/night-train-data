from .common import OperatorAdapter

class SncfAdapter(OperatorAdapter, operator_id="SNCF"):
    FIND_BOT_TRAINS_IN_GTFS = """
    SELECT BoT.trip_short_name as BoT_trip_name,
        trips.trip_headsign as SNCF_trip_name
    FROM BoT LEFT JOIN trips ON trips.trip_headsign = replace(BoT.trip_short_name, "IC Nuit ", "")
    WHERE (BoT.trip_short_name is NULL or instr(BoT.trip_short_name , "IC Nuit") )
        AND (trips.trip_headsign is NOT NULL OR BoT.trip_short_name is not null)
    GROUP BY BoT.trip_short_name, trips.route_id
    ORDER BY BoT.trip_short_name
    """