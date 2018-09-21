import collections
import csv

from cell import Cell
from station import Station

BASE_BOARD_FILE = "base-board.csv"

class BoardSpace(object):
    @staticmethod
    def parse(board_tile_args):
        name = board_tile_args["name"]
        cell = Cell.from_coord(board_tile_args["cells"])
        phase = int(board_tile_args["phase"]) if board_tile_args["phase"] else None
        capacity = int(board_tile_args["capacity"]) if board_tile_args["capacity"] else None
        return name, cell, phase, capacity

    def __init__(self, name, cell, phase, edges):
        self.name = name
        self.cell = cell
        self.edges = edges
        self.phase = phase

class Track(BoardSpace):
    @staticmethod
    def create(board_tile_args):
        # A track tile won't have a name or capacity, so we can ignore them
        _, cell, phase, _ = BoardSpace.parse(board_tile_args)
        
        paths = collections.defaultdict(list)
        for edge_str in board_tile_args["edges"].split(','):
            edge = [edge_val.strip() for edge_val in edge_str.split('-')]
            paths[edge[0]].append(edge[1])
            paths[edge[1]].append(edge[0])
        
        return Track(cell, phase, paths)

    def __init__(self, cell, phase, paths):
        super(Track, self).__init__(None, cell, None, tuple(paths.keys()))
        
        self.paths = paths

    def is_city(self):
        return False

class City(BoardSpace):
    @staticmethod
    def create(board_tile_args):
        name, cell, phase, capacity = BoardSpace.parse(board_tile_args)

        value = int(board_tile_args["value"])

        neighbors = {cell.neighbors[int(side.strip())] for side in board_tile_args["edges"].split(',')} if board_tile_args["edges"] else {}

        paths = collections.defaultdict(list)
        for neighbor in neighbors:
            paths[neighbor].extend(list(neighbors - {neighbor}))
        
        '''
        paths = collections.defaultdict(list)
        for start, ends in tile.paths.items():
            start_cell = cell.neighbors[PlacedTile._rotate(start, orientation)]
            start_tile = board.get_space(start_cell)
            if start_tile and cell in start_tile.neighbors:
                for end in ends:
                    end_cell = cell.neighbors[PlacedTile._rotate(end, orientation)]
                    end_tile = board.get_space(end_cell)
                    if end_tile and cell in end_tile.neighbors:
                        paths[start_cell].append(end_cell)
        '''
        
        return City(name, cell, phase, paths, neighbors, value, capacity)

    def __init__(self, name, cell, phase, paths, neighbors, value, capacity):
        super(City, self).__init__(name, cell, phase, tuple(paths.keys()))
        
        self.paths = paths
        self.neighbors = neighbors
        self._value = value
        self.capacity = capacity
        self._stations = []

    @property
    def stations(self):
        return tuple(self._stations)

    def value(self, phase):
        return self._value

    def has_station(self, railroad_name):
        return any(True for station in self._stations if station.railroad.name == railroad_name)

    def add_station(self, cell, railroad):
        self._stations.append(Station(cell, railroad))

    def is_city(self):
        return True

    def passable(self, railroad):
        return self.capacity - len(self.stations) > 0 or self.has_station(railroad.name)


class BoardEdge(BoardSpace):
    @staticmethod
    def create(board_tile_args):
        # This will never have capacity or a phase, so we can ignore them
        name, cell, _, _ = BoardSpace.parse(board_tile_args)

        paths = {cell.neighbors[int(side.strip())]: [] for side in board_tile_args["edges"].split(',')}
        neighbors = set(paths.keys())
        value_tuple = [int(val) for val in board_tile_args["value"].split(',')]
        board_edge_args = (name, cell, paths, neighbors, value_tuple)

        if board_tile_args["type"] == "edge":
            return BoardEdge(*board_edge_args)
        elif board_tile_args["type"] == "east":
            return EastEdge(*board_edge_args)
        elif board_tile_args["type"] == "west":
            return WestEdge(*board_edge_args)

    def __init__(self, name, cell, paths, neighbors, value_tuple):
        super(BoardEdge, self).__init__(name, cell, None, tuple(paths.keys()))

        self.paths = paths
        self.neighbors = neighbors
        self.phase1_value, self.phase3_value = value_tuple

    def value(self, phase):
        return self.phase1_value if phase in (1, 2) else self.phase3_value

    def is_city(self):
        return True

    def passable(self, railroad):
        return False

class EastEdge(BoardEdge):
    def __init__(self, name, cell, edges, neighbors, value_tuple):
        phase_values, self.bonus = value_tuple[:2], value_tuple[2]

        super(EastEdge, self).__init__(name, cell, edges, neighbors, phase_values)

    def value(self, phase, east_to_west=False):
        return super(EastEdge, self).value(phase) + (self.bonus if east_to_west else 0)

class WestEdge(BoardEdge):
    def __init__(self, name, cell, edges, neighbors, value_tuple):
        phase_values, self.bonus = value_tuple[:2], value_tuple[2]

        super(WestEdge, self).__init__(name, cell, edges, neighbors, phase_values)

    def value(self, phase, east_to_west=False):
        return super(WestEdge, self).value(phase) + (self.bonus if east_to_west else 0)


def load():
    board_tiles = []
    with open(BASE_BOARD_FILE, newline='') as board_file:
        for base_board_args in csv.DictReader(board_file, delimiter=';', skipinitialspace=True):
            if base_board_args["type"] == "track":
                board_tiles.append(Track.create(base_board_args))
            elif base_board_args["type"] == "city":
                board_tiles.append(City.create(base_board_args))
            elif base_board_args["type"] == "chicago":
                pass
            elif base_board_args["type"] in ("edge", "east", "west"):
                board_tiles.append(BoardEdge.create(base_board_args))
    return board_tiles