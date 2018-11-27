import argparse
import logging
import sys

from routes1846 import boardstate, find_best_routes, railroads


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("active-railroad",
            help="The name of the railroad for whom to find the route. Must be present in the railroads file.")
    parser.add_argument("board-state-file",
            help=("CSV file containing the board state. Semi-colon is the column separator. "
                  "The columns are: coord; tile_id; orientation"))
    parser.add_argument("railroads-file",
            help=("CSV file containing the board state. Semi-colon is the column separator. "
                  "The columns are: name; trains; stations; chicago_station_exit"))
    parser.add_argument("-v", "--verbose", action="store_true")
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = parse_args()

    logger = logging.getLogger("routes1846")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG if args["verbose"] else logging.INFO)

    board = boardstate.load_from_csv(args["board-state-file"])
    railroads = railroads.load_from_csv(board, args["railroads-file"])
    board.validate()

    best_routes = find_best_routes(board, railroads, railroads[args["active-railroad"]])
    print("RESULT")
    for route in best_routes:
        print("{}: {} ({})".format(route.train, route, route.value))