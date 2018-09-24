import itertools

import boardtile
from cell import Cell, CHICAGO_CELL
from placedtile import Chicago, PlacedTile
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
        if cell == CHICAGO_CELL:
            raise ValueError("Since Chicago ({}) is a special tile, please use Board.place_chicago().".format(CHICAGO_CELL))

        old_tile = self._placed_tiles.get(cell) or self._board_tiles.get(cell)
        if old_tile:
            new_tile = PlacedTile(cell, tile, int(orientation), capacity=old_tile.capacity, stations=old_tile.stations)
        else:
            new_tile = PlacedTile(cell, tile, int(orientation))
        self._placed_tiles[cell] = new_tile

    def place_station(self, coord, railroad):
        cell = Cell.from_coord(coord)
        if cell == CHICAGO_CELL:
            raise ValueError("Since Chicago ({}) is a special tile, please use Board.place_chicago_station().".format(CHICAGO_CELL))

        tile = self._placed_tiles.get(cell) or self._board_tiles.get(cell)
        tile.add_station(railroad)

    def place_chicago(self, tile):
        cell = CHICAGO_CELL
        old_tile = self._placed_tiles.get(cell) or self._board_tiles.get(cell)
        new_tile = Chicago(tile, old_tile.capacity, old_tile.exit_cell_to_station)
        self._placed_tiles[cell] = new_tile

    def place_chicago_station(self, railroad, exit_coord):
        chicago = self.get_space(CHICAGO_CELL)
        exit_cell = Cell.from_coord(exit_coord)
        chicago.add_station(railroad, exit_cell)

    def stations(self, railroad_name=None):
        all_tiles = list(self._placed_tiles.values()) + list(self._board_tiles.values())
        all_stations = itertools.chain.from_iterable([tile.stations for tile in all_tiles if isinstance(tile, (boardtile.City, PlacedTile))])
        if railroad_name:
            return tuple([station for station in all_stations if station.railroad.name == railroad_name])
        else:
            return tuple(all_stations)

    def get_space(self, cell):
        return self._placed_tiles.get(cell) or self._board_tiles.get(cell)