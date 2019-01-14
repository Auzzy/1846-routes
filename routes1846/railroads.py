import csv
import itertools

from routes1846.tokens import Station
from routes1846.cell import CHICAGO_CELL, Cell

RAILROAD_FIELDNAMES = ("name", "trains", "stations", "chicago_station_exit_coord")
PRIVATE_COMPANY_FIELDNAMES = ("port_coord", "meat_packing_coord", "has_mail_contract")
FIELDNAMES = RAILROAD_FIELDNAMES + PRIVATE_COMPANY_FIELDNAMES
TRAIN_TO_PHASE = {
    (2, 2): 1,
    (3, 5): 2,
    (4, 4): 2,
    (4, 6): 3,
    (5, 5): 3,
    (6, 6): 4,
    (7, 8): 4
}

class Train(object):
    @staticmethod
    def create(train_str):
        parts = train_str.split("/")
        collect = int(parts[0].strip())
        visit = int((parts[0] if len(parts) == 1 else parts[1]).strip())

        if (collect, visit) not in TRAIN_TO_PHASE:
            train_str = ", ".join(sorted(TRAIN_TO_PHASE.keys()))
            raise ValueError("Invalid train string found. Got ({}, {}), but expected one of {}".format(collect, visit, train_str))
        
        return Train(collect, visit, TRAIN_TO_PHASE[(collect, visit)])

    def __init__(self, collect, visit, phase):
        self.collect = collect
        self.visit = visit
        self.phase = phase

    def __str__(self):
        if self.collect == self.visit:
            return str(self.collect)
        else:
            return "{} / {}".format(self.collect, self.visit)

    def __hash__(self):
        return hash((self.phase, self.collect, self.visit))

    def __eq__(self, other):
        return isinstance(other, Train) and \
                self.phase == other.phase and \
                self.collect == other.collect and \
                self.visit == other.visit

class Railroad(object):
    @staticmethod
    def create(name, trains_str, has_mail_contract_raw=False):
        trains = [Train.create(train_str) for train_str in trains_str.split(",") if train_str] if trains_str else []

        has_mail_contract = has_mail_contract_raw is True or has_mail_contract_raw == "True"
        return Railroad(name, trains, has_mail_contract)

    def __init__(self, name, trains, has_mail_contract):
        self.name = name
        self.trains = trains
        self.has_mail_contract = has_mail_contract


def load_from_csv(board, railroads_filepath):
    with open(railroads_filepath, newline='') as railroads_file:
        return load(board, csv.DictReader(railroads_file, fieldnames=FIELDNAMES, delimiter=';', skipinitialspace=True))

def load(board, railroads_rows):
    railroads = {}
    for railroad_args in railroads_rows:
        railroad = Railroad.create(railroad_args["name"], railroad_args.get("trains"), railroad_args.get("has_mail_contract"))
        railroads[railroad.name] = railroad

        station_coords_str = railroad_args.get("stations")
        if station_coords_str:
            station_coords = [coord.strip() for coord in station_coords_str.split(",")]
            for coord in station_coords:
                if coord and Cell.from_coord(coord) != CHICAGO_CELL:
                    board.place_station(coord, railroad)

            if str(CHICAGO_CELL) in station_coords:
                chicago_station_exit_coord = str(railroad_args.get("chicago_station_exit_coord", "")).strip()
                if not chicago_station_exit_coord:
                    raise ValueError("Chicago is listed as a station for {}, but not exit side was specified.".format(railroad.name))
    
                board.place_chicago_station(railroad, int(chicago_station_exit_coord))

        port_coord = railroad_args.get("port_coord")
        if port_coord:
            board.place_seaport_token(port_coord, railroad)

        meat_coord = railroad_args.get("meat_packing_coord")
        if meat_coord:
            board.place_meat_packing_token(meat_coord, railroad)

    return railroads