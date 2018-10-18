import csv
import itertools

from routes1846.station import Station
from routes1846.cell import CHICAGO_CELL, Cell

FIELDNAMES = ("name", "trains", "stations", "chicago_station_exit_coord")
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

class Railroad(object):
    @staticmethod
    def create(name, trains_str):
        trains = [Train.create(train_str) for train_str in trains_str.split(",") if train_str] if trains_str else []
        return Railroad(name, trains)

    def __init__(self, name, trains):
        self.name = name
        self.trains = trains


def load_from_csv(board, railroads_filepath):
    with open(railroads_filepath, newline='') as railroads_file:
        return load(board, csv.DictReader(railroads_file, fieldnames=FIELDNAMES, delimiter=';', skipinitialspace=True))

def load(board, railroads_rows):
    railroads = {}
    for railroad_args in railroads_rows:
        railroad = Railroad.create(railroad_args["name"], railroad_args.get("trains"))
        railroads[railroad.name] = railroad

        station_coords_str = railroad_args.get("stations")
        if station_coords_str:
            station_coords = station_coords_str.split(",")
            for coord in station_coords:
                coord = coord.strip()
                if coord and Cell.from_coord(coord) != CHICAGO_CELL:
                    board.place_station(coord, railroad)

            if str(CHICAGO_CELL) in station_coords:
                chicago_station_exit_coord = str(railroad_args.get("chicago_station_exit_coord", "")).strip()
                if not chicago_station_exit_coord:
                    raise ValueError("Chicago is listed as a station for {}, but not exit side was specified.".format(railroad.name))
    
                board.place_chicago_station(railroad, int(chicago_station_exit_coord))

    return railroads