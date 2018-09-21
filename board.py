import itertools

import boardtile
from cell import Cell
from placedtile import PlacedTile
from station import Station

class Board(object):
    @staticmethod
    def load():
        board_tiles = {board_tile.cell: board_tile for board_tile in boardtile.load()}
        return Board(board_tiles)

    def __init__(self, board_tiles):
        self._board_tiles = board_tiles
        self._placed_tiles = {}

    def place_tile(self, coord, tile, orientation):
        cell = Cell.from_coord(coord)
        old_tile = self._placed_tiles.get(cell) or self._board_tiles.get(cell)
        if old_tile:
            new_tile = PlacedTile(cell, tile, int(orientation), capacity=old_tile.capacity, stations=old_tile.stations)
        else:
            new_tile = PlacedTile(cell, tile, int(orientation))
        self._placed_tiles[cell] = new_tile

    def place_station(self, coord, railroad):
        cell = Cell.from_coord(coord)
        tile = self._placed_tiles.get(cell) or self._board_tiles.get(cell)
        tile.add_station(cell, railroad)

    def stations(self, railroad_name=None):
        all_tiles = list(self._placed_tiles.values()) + list(self._board_tiles.values())
        all_stations = itertools.chain.from_iterable([tile.stations for tile in all_tiles if isinstance(tile, (boardtile.City, PlacedTile))])
        if railroad_name:
            return tuple([station for station in all_stations if station.railroad.name == railroad_name])
        else:
            return tuple(all_stations)

    def get_space(self, cell):
        return self._placed_tiles.get(cell) or self._board_tiles.get(cell)