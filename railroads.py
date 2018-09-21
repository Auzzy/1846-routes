import csv

from station import Station

class Train(object):
    @staticmethod
    def create(train_str):
        parts = train_str.split("/")
        collect = int(parts[0].strip())
        visit = int((parts[0] if len(parts) == 1 else parts[1]).strip())
        return Train(collect, visit)

    def __init__(self, collect, visit):
        self.collect = collect
        self.visit = visit

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
        for railroad_args in csv.DictReader(railroads_file, delimiter=';', skipinitialspace=True):
            railroad = Railroad.create(railroad_args["name"], railroad_args["trains"])
            railroads[railroad.name] = railroad
            
            for coord in railroad_args["stations"].split(","):
                if coord:
                    board.place_station(coord.strip(), railroad)

    return railroads