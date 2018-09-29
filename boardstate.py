import csv

from board import Board
from tiles import get_tile

FIELDNAMES = ("coord", "tile_id", "orientation")

def load(board_state_filepath="board-state.csv"):
    board = Board.load()    

    with open(board_state_filepath, newline='') as tiles_file:
        tile_args_dicts = []
        for tile_args in csv.DictReader(tiles_file, fieldnames=FIELDNAMES, delimiter=';', skipinitialspace=True):
            tile_args["tile"] = get_tile(tile_args.pop("tile_id"))
            tile_args_dicts.append(tile_args)

        for tile_args in sorted(tile_args_dicts, key=lambda adict: adict["tile"].phase):
            if tile_args["tile"].is_chicago:
                board.place_chicago(tile_args["tile"])
            else:
                board.place_tile(**tile_args)

    return board