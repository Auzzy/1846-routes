import itertools

from routes1846 import boardtile
from routes1846.cell import Cell, CHICAGO_CELL
from routes1846.placedtile import Chicago, PlacedTile
from routes1846.station import Station

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
        if cell == CHICAGO_CELL or tile.is_chicago:
            raise ValueError("Since Chicago ({}) is a special tile, please use Board.place_chicago().".format(CHICAGO_CELL))

        old_tile = self.get_space(cell)

        if int(orientation) not in range(1, 7):
            raise ValueError("Orientation out of range. Expected between 1 and 6, inclusive. Got {}.".format(orientation))

        if old_tile and old_tile.is_terminal_city:
            raise ValueError("Cannot upgrade the terminal cities.")

        if not old_tile or not old_tile.is_city:
            if tile.is_city or tile.is_z:
                tile_type = "Z city" if tile.is_z else "city"
                raise ValueError("{} is a track space, but you placed a {} ({}).".format(cell, tile_type, tile.id))
        elif old_tile.is_z:
            if not tile.is_z:
                tile_type = "city" if tile.is_city else "track"
                raise ValueError("{} is a Z city space, but you placed a {} ({}).".format(cell, tile_type, tile.id))
        elif old_tile.is_city:
            if not tile.is_city or tile.is_z:
                tile_type = "Z city" if tile.is_z else "track"
                raise ValueError("{} is a regular city space, but you placed a {} ({}).".format(cell, tile_type, tile.id))

        if old_tile:
            if old_tile.phase is None:
                raise ValueError("{} cannot be upgraded.".format(cell))
            elif old_tile.phase >= tile.phase:
                raise ValueError("{}: Going from phase {} to phase {} is not an upgrade.".format(cell, old_tile.phase, tile.phase))

            new_tile = PlacedTile.place(old_tile.name, cell, tile, orientation, stations=old_tile.stations)

            for old_start, old_ends in old_tile._paths.items():
                old_paths = tuple([(old_start, end) for end in old_ends])
                new_paths = tuple([(start, end) for start, ends in new_tile._paths.items() for end in ends])
                if not all(old_path in new_paths for old_path in old_paths):
                    raise ValueError("The new tile placed on {} does not preserve all the old paths.".format(cell))
        else:
            new_tile = PlacedTile.place(None, cell, tile, orientation)

        self._placed_tiles[cell] = new_tile

    def place_station(self, coord, railroad):
        cell = Cell.from_coord(coord)
        if cell == CHICAGO_CELL:
            raise ValueError("Since Chicago ({}) is a special tile, please use Board.place_chicago_station().".format(CHICAGO_CELL))

        tile = self.get_space(cell)
        if not tile.is_city:
            raise ValueError("{} is not a city, so it cannot have a station.".format(cell))

        tile.add_station(railroad)

    def place_chicago(self, tile):
        cell = CHICAGO_CELL
        old_tile = self._placed_tiles.get(cell) or self._board_tiles.get(cell)
        if not old_tile.phase or old_tile.phase >= tile.phase:
            raise ValueError("{}: Going from phase {} to phase {} is not an upgrade.".format(cell, old_tile.phase, tile.phase))

        new_tile = Chicago.place(tile, old_tile.exit_cell_to_station)
        self._placed_tiles[cell] = new_tile

    def place_chicago_station(self, railroad, exit_side):
        chicago = self.get_space(CHICAGO_CELL)
        exit_cell = CHICAGO_CELL.neighbors[exit_side]
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

    def validate(self):
        invalid = []
        for cell, placed_tile in self._placed_tiles.items():
            if not placed_tile.stations:
                for neighbor_cell in placed_tile.paths():
                    neighbor = self.get_space(neighbor_cell)
                    if neighbor and cell in neighbor.paths():
                        break
                else:
                    invalid.append(cell)
        
        if invalid:
            invalid_str = ", ".join([str(cell) for cell in invalid])
            raise ValueError("Tiles at the following spots have no neighbors and no stations: {}".format(invalid_str))

        '''
        print("SPACE: " + str(cell))
        valid = False
        if new_tile.stations:
            valid = True
        else:
            for neighbor_cell in new_tile.paths():
                neighbor = self.get_space(neighbor_cell)
                if neighbor and cell in neighbor.paths():
                    valid = True
        print("VALID? " + str(valid))
        '''