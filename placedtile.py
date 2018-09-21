import collections

from cell import Cell
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

        self.paths = {}
        for start, ends in tile.paths.items():
            start_cell = self.cell.neighbors[self._rotate(start, orientation)]
            self.paths[start_cell] = tuple([cell.neighbors[self._rotate(end, orientation)] for end in ends])

    def add_station(self, cell, railroad):
        self._stations.append(Station(cell, railroad))

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

    def has_station(self, railroad_name):
        return any(True for station in self._stations if station.railroad.name == railroad_name)