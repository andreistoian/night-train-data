import pandas as pd
from .utils import *
from typing import Dict


class OperatorAdapter:

    operator_id: str

    def __init__(self, BoT_dataframe: pd.DataFrame, datasource: str):
        assert isinstance(datasource, str)

        _, ext = os.path.splitext(datasource)

        if ext == ".zip":
            temp_dir = tempfile.mkdtemp(prefix="gtfs_")
            db_dir = tempfile.mkdtemp(prefix="gtfs_")
            self.db_file = os.path.join(
                db_dir, "gtfs_database.sqlite"
            )  # SQLite database file

            print(f"Importing {datasource} to {self.db_file}")

            ensure_dir(db_dir)

            extract_gtfs(datasource, temp_dir)
            import_gtfs_to_sqlite(self.db_file, temp_dir)

            add_bot_table(self.db_file, BoT_dataframe)

    def __init_subclass__(cls, operator_id, **kwargs):
        super().__init_subclass__(**kwargs)
        OPERATOR_ADAPTERS[operator_id] = cls

    def find_matching_bot_trains(self):
        assert False, "Not implemented"

    def get_train_timetable(self, operator_train_id):
        assert False, "Not implemented"

    def unique_days_of_week(self, operator_train_id):
        assert False, "Not implemented"

    def extract_operator_format_train_ids(self, route_short_name):
        return route_short_name


OPERATOR_ADAPTERS: Dict[str, OperatorAdapter] = {}
