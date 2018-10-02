import argparse

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
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = parse_args()
    board = boardstate.load_from_csv(args["board-state-file"])
    railroads = railroads.load_from_csv(board, args["railroads-file"])
    board.validate()

    best_routes = find_best_routes(board, railroads, railroads[args["active-railroad"]])
    for train, route_and_value in best_routes.items():
        print("{}: {} ({})".format(train, *route_and_value))