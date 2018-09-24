import collections
import json

from cell import Cell, CHICAGO_CELL
from station import Station

BASE_BOARD_FILE = "base-board.json"

class BoardSpace(object):
    def __init__(self, name, cell, phase, paths):
        self.name = name
        self.cell = cell
        self.phase = phase
        self._paths = paths

    def paths(self, enter_from=None, railroad=None):
        if enter_from:
            return self._paths[enter_from]
        else:
            return tuple(self._paths.keys())

class Track(BoardSpace):
    @staticmethod
    def create(coord, edges, phase=None):
        cell = Cell.from_coord(coord)
        
        paths = collections.defaultdict(list)
        for start, end in edges:
            paths[start].append(end)
            paths[end].append(start)

        return Track(cell, phase, paths)

    def __init__(self, cell, phase, paths):
        super(Track, self).__init__(None, cell, None, paths)

    def is_city(self):
        return False

class City(BoardSpace):
    @staticmethod
    def create(coord, name, phase=None, edges=[], value=0, capacity=0, is_z=False):
        cell = Cell.from_coord(coord)

        neighbors = {cell.neighbors[side] for side in edges}

        if cell == CHICAGO_CELL:
            paths = {cell.neighbors[side]: [] for side in edges}
            return Chicago(phase, paths, neighbors, value, capacity)
        else:
            paths = {neighbor: list(neighbors - {neighbor}) for neighbor in neighbors}
            return City(name, cell, phase, paths, neighbors, value, capacity)

    def __init__(self, name, cell, phase, paths, neighbors, value, capacity):
        super(City, self).__init__(name, cell, phase, paths)

        self.neighbors = neighbors
        self._value = value
        self.capacity = capacity
        self._stations = []

    @property
    def stations(self):
        return tuple(self._stations)

    def value(self, phase):
        return self._value

    def add_station(self, railroad):
        station = Station(self.cell, railroad)
        self._stations.append(station)
        return station

    def get_station(self, railroad_name):
        for station in self._stations:
            if station.railroad.name == railroad_name:
                return station
        return None

    def has_station(self, railroad_name):
        return bool(self.get_station(railroad_name))

    def is_city(self):
        return True

    def passable(self, railroad):
        return self.capacity - len(self.stations) > 0 or self.has_station(railroad.name)

class Chicago(City):
    def __init__(self, phase, paths, neighbors, value, capacity):
        super(Chicago, self).__init__("Chicago", CHICAGO_CELL, phase, paths, neighbors, value, capacity)

        self.exit_cell_to_station = {}

    def add_station(self, railroad, exit_cell):
        station = super(Chicago, self).add_station(self.cell, railroad)
        self.exit_cell_to_station[exit_cell] = station
        return station

    def passable(self, railroad):
        return False

class BoardEdge(BoardSpace):
    @staticmethod
    def create(coord, name, edges, values, is_east=False, is_west=False):
        cell = Cell.from_coord(coord)

        paths = {cell.neighbors[side]: [] for side in edges}
        neighbors = set(paths.keys())

        if is_east:
            return EastEdge(name, cell, paths, neighbors, values)
        elif is_west:
            return WestEdge(name, cell, paths, neighbors, values)
        else:
            return BoardEdge(name, cell, paths, neighbors, values)

    def __init__(self, name, cell, paths, neighbors, value_dict):
        super(BoardEdge, self).__init__(name, cell, None, paths)

        self.neighbors = neighbors
        self.phase1_value = value_dict["phase1"]
        self.phase3_value = value_dict["phase3"]

    def value(self, phase):
        return self.phase1_value if phase in (1, 2) else self.phase3_value

    def is_city(self):
        return True

    def passable(self, railroad):
        return False

class EastEdge(BoardEdge):
    def __init__(self, name, cell, paths, neighbors, value_dict):
        super(EastEdge, self).__init__(name, cell, paths, neighbors, value_dict)
        
        self.bonus = value_dict["bonus"]

    def value(self, phase, east_to_west=False):
        return super(EastEdge, self).value(phase) + (self.bonus if east_to_west else 0)

class WestEdge(BoardEdge):
    def __init__(self, name, cell, paths, neighbors, value_dict):
        super(WestEdge, self).__init__(name, cell, paths, neighbors, value_dict)
        
        self.bonus = value_dict["bonus"]

    def value(self, phase, east_to_west=False):
        return super(WestEdge, self).value(phase) + (self.bonus if east_to_west else 0)

def load():
    board_tiles = []
    with open(BASE_BOARD_FILE) as board_file:
        board_json = json.load(board_file)
        board_tiles.extend([Track.create(coord, **track_args) for coord, track_args in board_json["tracks"].items()])
        board_tiles.extend([City.create(coord, **city_args) for coord, city_args in board_json["cities"].items()])
        board_tiles.extend([BoardEdge.create(coord, **board_edge_args) for coord, board_edge_args in board_json["edges"].items()])
    return board_tiles