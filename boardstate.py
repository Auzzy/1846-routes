import csv

from board import Board
from tiles import get_tile

FIELDNAMES = ("coord", "tile_id", "orientation")

def load(board_state_filepath="board-state.csv"):
    board = Board.load()

    with open(board_state_filepath, newline='') as tiles_file:
        for tiles_args in csv.DictReader(tiles_file, fieldnames=FIELDNAMES, delimiter=';', skipinitialspace=True):
            tiles_args["tile"] = get_tile(tiles_args.pop("tile_id"))
            if tiles_args["tile"].is_chicago:
                board.place_chicago(tiles_args["tile"])
            else:
                board.place_tile(**tiles_args)

    return board