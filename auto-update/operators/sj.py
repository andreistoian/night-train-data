from .common import OperatorAdapter

class SJAdapter(OperatorAdapter, operator_id="SJ"):
    FIND_BOT_TRAINS_IN_GTFS = """
    SELECT * FROM 
        BoT JOIN 
            (routes INNER JOIN Trips on routes.route_id = trips.route_id) RT 
            ON BoT.trip_short_name LIKE '%' || RT.trip_short_name || '%'
    Where BoT.agency_id = 'SJ'
    GROUP BY RT.trip_short_name
    """
