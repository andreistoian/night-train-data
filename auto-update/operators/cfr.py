from .common import OperatorAdapter


class CFRAdapter(OperatorAdapter, operator_id="CFR"):
    def __init__(self, BoT_dataframe, datasource):
        super().__init__(BoT_dataframe, datasource)

        self.xml_file = datasource
        assert (
            isinstance(datasource, str) and ".xml" in datasource
        ), "Romania adapter works only on XML files"
        self.bot_df = BoT_dataframe

    def find_matching_bot_trains(self):
        return self.cfr_find_irn_trains(self.xml_file)

    #        results = []
    #        for train_number in df_irn_cfr["Train Number"]:
    #            train_route = cfr_get_train_route(schedule_file, train_number)
    #            first_station, first_departure, last_station, last_arrival = cfr_get_train_timings(train_route)
    ##            results.append({
    #                "Train Number": train_number,
    #                "Departure": first_station,
    #                "Departure Time": first_departure,
    #                "Arrival": last_station,
    #                "Arrival Time": last_arrival,
    #            })

    def cfr_get_train_route(xml_file, train_number):
        """Fetches route details for a specific train number, excluding zero-stop entries."""
        # Parse the XML file
        tree = etree.parse(xml_file)

        # Find the train with the given number
        train = tree.xpath(f"//Tren[@Numar='{train_number}']")
        if not train:
            print(f"Train {train_number} not found.")
            return pd.DataFrame()  # Return empty DataFrame if train not found

        train = train[0]  # Get the first matching train

        # Find all <ElementTrasa> elements
        elements = train.xpath(".//ElementTrasa")

        # Extract relevant data, filtering out entries where StationareSecunde == "0"
        data = []
        for elem in elements:
            departure_station = elem.get("DenStaOrigine")
            arrival_station = elem.get("DenStaDestinatie")
            departure_time = convert_seconds_to_time(elem.get("OraP"))
            arrival_time = convert_seconds_to_time(elem.get("OraS"))
            stop_time = int(elem.get("StationareSecunde", "0"))

            data.append(
                {
                    "Arrival Station": arrival_station,
                    "Arrival Time": arrival_time,
                    "Departure Station": departure_station,
                    "Departure Time": departure_time,
                    "Stop Time (Sec)": stop_time,
                }
            )

        # Convert to Pandas DataFrame
        df = pd.DataFrame(data)

        return df

    def cfr_get_train_timings(train_route):
        """Finds the first station's departure time, last station's arrival time,
        first station name, and last station name."""
        if train_route.empty:
            return None, None, None, None

        first_station = train_route.iloc[0]["Departure Station"]
        first_departure = train_route.iloc[0]["Departure Time"]
        last_station = train_route.iloc[-1]["Arrival Station"]
        last_arrival = train_route.iloc[-1]["Arrival Time"]

        return first_station, first_departure, last_station, last_arrival

    def cfr_find_irn_trains(xml_file):
        """Parses an XML file and returns a DataFrame with train numbers where CategorieTren='IR-N'."""
        # Parse the XML file
        tree = etree.parse(xml_file)

        # Find all trains with CategorieTren="IR-N"
        trains = tree.xpath("//Tren[@CategorieTren='IR-N']")

        # Extract train numbers
        train_numbers = [train.get("Numar") for train in trains]

        # Convert to DataFrame
        df = pd.DataFrame(train_numbers, columns=["Train Number"])

        return df
