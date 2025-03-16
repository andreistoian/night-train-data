import sqlite3
import zipfile
import os
import pandas as pd
import tempfile
from lxml import etree
from datetime import timedelta
import time
import re
import urllib
import requests
from bs4 import BeautifulSoup

from .common import OperatorAdapter


class UkraineAdapter(OperatorAdapter, operator_id="UK"):
    def __init__(self, BoT_dataframe, datasource):
        super().__init__(BoT_dataframe, datasource)

        self.df = BoT_dataframe

        if os.path.exists(datasource):
            pass
        else:
            df_all_trains = self.get_all_night_trains_in_bot_db()
            df_all_trains.to_csv(datasource)

        pass

    def _parse_train_table(self, html_content):
        """Extract train information from an HTML page and return it as a DataFrame."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the specific <div> containing the table
        caption_div = soup.find("div", class_="caption")
        if not caption_div:
            print("No caption div found.")
            return pd.DataFrame()

        # Find the adjacent <table> after the caption div
        table = caption_div.find_next("table")
        if not table:
            print("No table found after caption div.")
            return pd.DataFrame()

        # Extract table headers
        headers = [th.get_text(strip=True) for th in table.find_all("th")]

        # Extract table rows
        rows = []
        for tr in table.find_all("tr")[1:]:  # Skip header row
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            rows.append(cells)

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=headers)
        return df

    def _get_trip_short_names(self):
        """Fetch distinct trip_short_name values from a CSV file where agency_id = 'UZ'."""
        df = self.df[self.df["agency_id"] == "UZ"]  # Filter where agency_id is 'UZ'

        def extract_number(value):
            """Extract the first occurring number from a string."""
            match = re.search(r"\d+", str(value))  # Find first number
            return match.group(0) if match else None  # Return the number or None

        df["trip_short_name"] = df["trip_short_name"].apply(
            extract_number
        )  # Apply extraction
        return (
            df["trip_short_name"].dropna().unique().tolist()
        )  # Get unique non-null numbers as

    def _fetch_train_name(self, trip_short_name):
        """Query the URL to fetch the list of train names."""
        base_url = "https://uz.gov.ua/en/passengers/timetable/suggest-train/?q="
        url = base_url + urllib.parse.quote(
            str(trip_short_name)
        )  # Encode trip_short_name

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            train_list = response.json()

            if not train_list:
                print(f"No results for {trip_short_name}")
                return None

            unique_trains = set(train_list)  # Remove duplicates

            return unique_trains  # Return the distinct train name

        except requests.RequestException as e:
            print(f"Error fetching data for {trip_short_name}: {e}")
            return None

    def _generate_train_url(self, train_name):
        """Encode and generate the final train URL."""
        if train_name:
            encoded_train_name = urllib.parse.quote(train_name)
            final_url = f"https://uz.gov.ua/en/passengers/timetable/?ntrain={encoded_train_name}&by_number=Search"
            return final_url
        return None

    def get_all_night_trains_in_bot_db(self):
        trip_names = self._get_trip_short_names()

        df_all_trains = None
        for trip_short_name in trip_names:
            distinct_trains = self._fetch_train_name(trip_short_name)

            if distinct_trains:
                for train_id in distinct_trains:
                    final_url = self._generate_train_url(train_id)

                    try:
                        response = requests.get(final_url, timeout=10)
                        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
                        html_content = response.text  # Get HTML content

                        # Call parse_train_table function to extract data
                        df_train = self._parse_train_table(html_content)
                        if df_all_trains is None:
                            df_all_trains = df_train
                        else:
                            df_all_trains = pd.concat(
                                [df_all_trains, df_train], ignore_index=True
                            )

                    except requests.RequestException as e:
                        print(f"Error fetching data for train {train_id}: {e}")

                    time.sleep(1)

        return df_all_trains

    def parse_train_table(html_content):
        """Extract train information from an HTML page and return it as a DataFrame."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the specific <div> containing the table
        caption_div = soup.find("div", class_="caption")
        if not caption_div:
            print("No caption div found.")
            return pd.DataFrame()

        # Find the adjacent <table> after the caption div
        table = caption_div.find_next("table")
        if not table:
            print("No table found after caption div.")
            return pd.DataFrame()

        # Extract table headers
        headers = [th.get_text(strip=True) for th in table.find_all("th")]

        # Extract table rows
        rows = []
        for tr in table.find_all("tr")[1:]:  # Skip header row
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            rows.append(cells)

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=headers)
        return df
