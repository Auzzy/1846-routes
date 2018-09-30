import csv
import itertools

from routes1846.station import Station

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
    def create(name, trains):
        trains = [Train.create(train_str) for train_str in trains.split(",")]
        return Railroad(name, trains)

    def __init__(self, name, trains):
        self.name = name
        self.trains = trains


def load(board, railroads_filepath="railroads.csv"):
    with open(railroads_filepath, newline='') as railroads_file:
        railroads = {}
        for railroad_args in csv.DictReader(railroads_file, fieldnames=FIELDNAMES, delimiter=';', skipinitialspace=True):
            railroad = Railroad.create(railroad_args["name"], railroad_args["trains"])
            railroads[railroad.name] = railroad
            
            for coord in railroad_args["stations"].split(","):
                coord = coord.strip()
                if coord:
                    board.place_station(coord, railroad)

            chicago_station_exit_coord = railroad_args["chicago_station_exit_coord"].strip()
            if chicago_station_exit_coord:
                board.place_chicago_station(railroad, chicago_station_exit_coord)

    return railroads