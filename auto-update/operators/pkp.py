from .common import OperatorAdapter


class PKPAdapter(OperatorAdapter, operator_id="PKP"):
    FIND_BOT_TRAINS_IN_GTFS = """
    SELECT DISTINCT BoT.trip_short_name as BoT_trip_name,
        trips.route_id || " " || trips.trip_short_name as gtfs_trip_name
    FROM BoT JOIN trips 
    WHERE INSTR(trips.route_id || " " || trips.trip_short_name, BoT.trip_short_name) > 0
        AND BoT.agency_id = "PKP"
    ORDER BY BoT.trip_short_name;
    """
