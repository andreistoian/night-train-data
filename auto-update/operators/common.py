import pandas
from .utils import *
from typing import Dict

class OperatorAdapter():

    operator_id: str

    def __init__(self, BoT_dataframe: pandas.DataFrame, datasource: str):
        assert isinstance(datasource, str)

        _, ext = os.path.splitext(datasource)

        if ext == ".zip":
            temp_dir = tempfile.mkdtemp(prefix="gtfs_")
            db_dir = tempfile.mkdtemp(prefix="gtfs_")
            db_file = os.path.join(db_dir, "gtfs_database.sqlite")  # SQLite database file
            print(f"Importing {datasource} to {db_file}")

            ensure_dir(db_dir)

            extract_gtfs(datasource, temp_dir)
            import_gtfs_to_sqlite(db_file, temp_dir)

            add_bot_table(db_file, BoT_dataframe)

    def __init_subclass__(cls, operator_id, **kwargs):
        super().__init_subclass__(**kwargs)
        OPERATOR_ADAPTERS[operator_id] = cls

    def find_matching_bot_trains(self):
        pass

    def get_train_timetable(self):
        # Can return multiple timetables
        pass
    
OPERATOR_ADAPTERS: Dict[str, OperatorAdapter] = {}
