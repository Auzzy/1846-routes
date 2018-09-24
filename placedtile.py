import collections

from cell import Cell, CHICAGO_CELL
from station import Station

class PlacedTile(object):
    @staticmethod
    def _rotate(side, orientation):
        # (side num) + (number of times rotated), then 0-indexed (by subtracting 1), perform mod 6 (number of sides), then 1-indexed (by adding 1)
        return ((side + (orientation - 1) - 1) % 6) + 1

    def __init__(self, cell, tile, orientation, capacity=None, stations=[]):
        self.cell = cell
        self.tile = tile
        self.capacity = capacity
        self._stations = list(stations)

        self._paths = {}
        for start, ends in tile.paths.items():
            start_cell = self.cell.neighbors[self._rotate(start, orientation)]
            self._paths[start_cell] = tuple([cell.neighbors[self._rotate(end, orientation)] for end in ends])

    def value(self, phase):
        return self.tile.value

    @property
    def is_city(self):
        return self.tile.is_city or self.tile.is_z or self.tile.is_chicago

    def passable(self, railroad):
        return self.capacity - len(self.stations) > 0 or self.has_station(railroad.name)

    @property
    def stations(self):
        return tuple(self._stations)

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

    def paths(self, enter_from=None, railroad=None):
        if enter_from:
            return self._paths[enter_from]
        else:
            return tuple(self._paths.keys())

class Chicago(PlacedTile):
    def __init__(self, tile, capacity, exit_cell_to_station={}):
        super(Chicago, self).__init__(CHICAGO_CELL, tile, 1, capacity, list(exit_cell_to_station.values()))
        
        self.exit_cell_to_station = exit_cell_to_station

    def paths(self, enter_from=None, railroad=None):
        paths = list(super(Chicago, self).paths(enter_from))
        if railroad:
            station = self.exit_cell_to_station.get(enter_from)
            if station:
                if station.railroad != railroad:
                    paths = []
            else:
                for exit in paths:
                    station = self.exit_cell_to_station.get(exit)
                    if station and station.railroad != railroad:
                        paths.remove(exit)
        return tuple(paths)

    def add_station(self, railroad, exit_cell):
        station = super(Chicago, self).add_station(railroad)
        self.exit_cell_to_station[exit_cell] = station
        return station