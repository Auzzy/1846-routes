import collections

from routes1846.cell import Cell, CHICAGO_CELL
from routes1846.station import Station

class PlacedTile(object):
    @staticmethod
    def _rotate(side, orientation):
        # (side num) + (number of times rotated), then 0-indexed (by subtracting 1), perform mod 6 (number of sides), then 1-indexed (by adding 1)
        return ((side + (orientation - 1) - 1) % 6) + 1

    @staticmethod
    def get_paths(cell, tile, orientation):
        paths = {}
        for start, ends in tile.paths.items():
            start_cell = cell.neighbors[PlacedTile._rotate(start, orientation)]
            paths[start_cell] = tuple([cell.neighbors[PlacedTile._rotate(end, orientation)] for end in ends])

        if None in paths:
            raise ValueError("Placing tile {} in orientation {} at {} goes off-map.".format(tile.id, orientation, cell))

        return paths

    @staticmethod
    def place(name, cell, tile, orientation, stations=[]):
        paths = {}
        for start, ends in tile.paths.items():
            start_cell = cell.neighbors[PlacedTile._rotate(start, orientation)]
            paths[start_cell] = tuple([cell.neighbors[PlacedTile._rotate(end, orientation)] for end in ends])

        # This will cause problems if B&O or PRR use their special station...
        if None in paths:
            raise ValueError("Placing tile {} in orientation {} at {} goes off-map.".format(tile.id, orientation, cell))

        return PlacedTile(name, cell, tile, orientation, stations, paths)

    def __init__(self, name, cell, tile, orientation, stations=[], paths={}):
        self.name = name or str(cell)
        self.cell = cell
        self.tile = tile
        self.capacity = tile.capacity
        self._stations = list(stations)
        self._paths = paths
        
        self.phase = self.tile.phase
        self.is_city = self.tile.is_city
        self.is_z = self.tile.is_z
        self.is_terminal_city = False

    def value(self, phase):
        return self.tile.value

    def passable(self, railroad):
        return self.capacity - len(self.stations) > 0 or self.has_station(railroad.name)

    @property
    def stations(self):
        return tuple(self._stations)

    def add_station(self, railroad):
        if self.has_station(railroad.name):
            raise ValueError("{} already has a station in {} ({}).".format(railroad.name, self.name, self.cell))

        if self.capacity <= len(self.stations):
            raise ValueError("{} ({}) cannot hold any more stations.".format(self.name, self.cell))

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
    @staticmethod
    def place(tile, exit_cell_to_station={}):
        paths = PlacedTile.get_paths(CHICAGO_CELL, tile, 1)
        return Chicago(tile, exit_cell_to_station, paths)

    def __init__(self, tile, exit_cell_to_station={}, paths={}):
        super(Chicago, self).__init__("Chicago", CHICAGO_CELL, tile, 1, list(exit_cell_to_station.values()), paths)
        
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
        if exit_cell not in self.paths():
            raise ValueError("Illegal exit cell for Chicago")

        station = super(Chicago, self).add_station(railroad)
        self.exit_cell_to_station[exit_cell] = station
        return station