# written: ben lipkin, aalok sathe

import os
import json
import itertools
from pathlib import Path
import pandas as pd

from flask import Flask, request, jsonify
from flask_cors import CORS


class DictPersistJSON(dict):
    """
    A dictionary subclass that persists its data to a JSON file.

    This class extends the built-in `dict` class and adds the ability to load and dump its data from/to a JSON file.

    Args:
        filename (str): The path to the JSON file.

    """

    def __init__(self, filename, *args, **kwargs):
        self.filename = filename
        self._load()
        self.update(*args, **kwargs)

    def _load(self):
        """
        Load data from the JSON file.

        If the file exists and is not empty, the data is loaded from the file and added to the dictionary.
        """
        if os.path.isfile(self.filename) and os.path.getsize(self.filename) > 0:
            with open(self.filename, "r") as fh:
                self.update(json.load(fh))

    def _dump(self):
        """
        Dump data to the JSON file.

        The current state of the dictionary is dumped to the file in JSON format.
        """
        with open(self.filename, "w+") as fh:
            json.dump(self, fh)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self._dump()

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return "%s(%s)" % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
        self._dump()


def initialize_stim_server(STIMULI_LISTS: Path, database_name: str = None) -> Flask:
    """
    Initializes the stimulus server.

    Args:
        STIMULI_LISTS (Path): The path to the directory containing the stimuli CSV files.
    """
    app = Flask(__name__)
    CORS(app)

    ################################################################################
    # load/define our stimuli in advance
    ################################################################################
    # stimuli are located in the provided directory as CSVs and contain many columns
    # with relevant metadata that needs preserving

    database_name = (
        database_name or f"{STIMULI_LISTS / STIMULI_LISTS.stem}-stim-db.json"
    )

    def csv_to_json_dicts(csv: Path) -> list[dict]:
        """
        Convert a pandas DataFrame to a list of dictionaries.

        Args:
            csv (pd.DataFrame): The DataFrame to convert.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary corresponds to a row in the DataFrame.
        """
        df = pd.read_csv(csv)
        return df.to_dict(orient="records")

    STIMULI = {}
    for p in Path(STIMULI_LISTS).glob("*.csv"):
        cid = int(p.stem[len("likert_") :])
        jd = csv_to_json_dicts(p)
        STIMULI[cid] = jd
    EPSILON = 1e-3

    ################################################################################
    # initialize the database from a file if it exists, else create a new one
    # with all counts set to 0
    ################################################################################
    INIT_DB = lambda: DictPersistJSON(
        database_name, **{str(i): 0.0 for i, _ in enumerate(STIMULI)}
    )

    def init_or_sync_db() -> DictPersistJSON:
        """
        Initialize the database from a file if it exists, else create a new one with all counts set to 0.

        Args:
            filename (str): The path to the JSON file.

        Returns:
            DictPersistJSON: The database.
        """
        DB_FILENAME = database_name

        if not os.path.isfile(DB_FILENAME):
            DATABASE = INIT_DB()
        else:
            DATABASE = DictPersistJSON(DB_FILENAME)

        return DATABASE

    @app.route("/start", methods=["GET"])
    def get_data_and_open_count():
        """
        Retrieves the stimulus with the lowest count and increments its count by EPSILON
        so that it doesn't get picked by another request and then returns the stimulus to the client in
        JSON format.
        If the client never sends a POST request to /complete, the count will remain incremented
        by EPSILON. However, it will still be used before any of the other stimuli that are indeed
        completed are used again.
        """
        print("get_data_and_open_count() called with method: GET")
        # reflect any manual changes made in the meantime...
        # ANY other changes ANYwhere within the code to the database are immediately propogated to disk
        DATABASE = init_or_sync_db()
        idx = min(DATABASE, key=DATABASE.get)
        DATABASE[idx] += EPSILON
        DATABASE._dump()
        return jsonify({"idx": idx, "stim": STIMULI[int(idx)]})

    @app.route("/complete", methods=["POST"])
    def complete_view_and_close_count():
        """
        When the client is done using the stimulus, it should send a POST request to
        this endpoint informing what stimulus it just finished using. Then we will
        subtract EPSILON but increase its count by 1 to mark it as used.
        """
        print("complete_view_and_close_count() called with method: POST")
        DATABASE = init_or_sync_db()
        idx = request.json["idx"]
        DATABASE[idx] += 1 - EPSILON
        DATABASE._dump()
        return "OK"

    # apparently this just returns the entire database?
    @app.route("/status", methods=["GET"])
    def get_current_progress_status():
        print("get_current_progress_status() called with method: GET")
        DATABASE = init_or_sync_db()
        return jsonify(DATABASE)

    @app.route("/reset", methods=["GET"])
    def reset_database():
        """
        Resets the database by reinitializing it and dumping its contents.

        Returns:
            str: A message indicating the success of the database reset.
        """
        print("reset_database() called with method: GET")
        # global DATABASE
        DATABASE = INIT_DB()
        DATABASE._dump()
        return "OK"

    @app.route("/", methods=["GET"])
    def test_connection():
        print("test_connection() called with method: GET")
        return "OK"

    print("stim server initialized")
    return app


from argparse import ArgumentParser

parser = ArgumentParser("EWoK human study server")
parser.add_argument(
    "--host",
    help="host to serve to",
    default="0.0.0.0",
)
parser.add_argument(
    "--port",
    help="port to bind the server to",
    default=8770,
)
parser.add_argument(
    "--database_name",
    help="path to the database file",
    required=False,
    default=None,
)

parser.add_argument(
    "--stimuli",
    help="path to the directory containing the stimuli CSV files, e.g. stims/{likert1, likert2, ...}.csv",
    type=Path,
    default="[REDACTED]/latin_sq_materials/social_properties/",
)

args = parser.parse_args()

print(args)
app = application = initialize_stim_server(
    STIMULI_LISTS=args.stimuli,
    database_name=args.database_name,
)

if __name__ == "__main__":
    from waitress import serve

    print(f"Starting server at http://{args.host}:{args.port}")
    serve(app, host=args.host, port=args.port)
