import argparse
import itertools

import boardstate
import railroads
from board import Board
from route import Route


def find_best_routes(route_by_train, railroad):
    if len(route_by_train) == 1:
        route_sets = [{train: (route, value)} for train, routes in route_by_train.items() for route, value in routes.items()]
    else:
        route_sets = []
        for route_set in itertools.product(*[route_to_value.keys() for route_to_value in route_by_train.values()]):
            for route1, route2 in itertools.combinations(route_set, 2):
                if route1.overlap(route2):
                    break
            else:
                route_sets.append({train: (route, route_by_train[train][route]) for train, route in zip(route_by_train.keys(), route_set)})
        
    return max(route_sets, key=lambda route_set: sum(value for route, value in route_set.values()))

def get_subroutes(routes, stations):
    subroutes = [route.subroutes(station.cell) for station in stations for route in routes]
    return set(itertools.chain.from_iterable([subroute for subroute in subroutes if subroute]))

def find_connected_cities(board, railroad, cell, dist):
    tiles = itertools.chain.from_iterable(walk_paths(board, railroad, None, cell, dist))
    return {tile.cell for tile in tiles if tile.is_city} - {cell}

def walk_paths(board, railroad, enter_from, cell, length, visited=None):
    visited = visited or []
    
    tile = board.get_space(cell)
    if not tile or (enter_from and enter_from not in tile.paths()) or tile in visited:
        return (Route.empty(), )

    if tile.is_city:
        if length - 1 == 0 or (enter_from and not tile.passable(railroad)):
            return (Route.single(tile), )

        remaining_cities = length - 1
    else:
        remaining_cities = length

    neighbors = tile.paths(enter_from, railroad) if enter_from else tile.paths()
    routes = []
    for neighbor in neighbors:
        neighbor_paths = walk_paths(board, railroad, cell, neighbor, remaining_cities, visited + [tile])
        for neighbor_path in neighbor_paths:
            if neighbor_path:
                routes.append(Route.single(tile).merge(neighbor_path))
    if not routes and tile.is_city:
        routes.append(Route.single(tile))
    return tuple(set(routes))


def find_paths(board, railroad, cell, train):
    tile = board.get_space(cell)
    if not tile.is_city:
        raise Exception("How is your station not in a city? {}".format(cell))

    return walk_paths(board, railroad, None, cell, train.visit)

def find_routes(board, railroad):
    stations = board.stations(railroad.name)

    routes = {}
    for train in railroad.trains:
        routes[train] = set()
        for station in stations:
            routes[train].update(find_paths(board, railroad, station.cell, train))

            connected_cities = find_connected_cities(board, railroad, station.cell, train.visit - 1)
            connected_paths = set()
            for cell in connected_cities:
                for path in find_paths(board, railroad, cell, train):
                    if path.contains_cell(station.cell):
                        connected_paths.add(path)

            routes[train].update(connected_paths)

        routes[train].update(get_subroutes(routes[train], stations))

    return routes

def detect_phase(railroads):
    return max([train.phase for railroad in railroads.values() for train in railroad.trains])

def calc_route(board, railroads, active_railroad):
    routes = find_routes(board, active_railroad)

    phase = detect_phase(railroads)
    route_by_train = {}
    for train in routes:
        route_by_train[train] = {route: route.value(train, phase) for route in routes[train]}
    
    best_route = find_best_routes(route_by_train, active_railroad)
    for train, route_and_value in best_route.items():
        print("{}: {} ({})".format(train, *route_and_value))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("active-railroad",
            help="The name of the railroad for whom to find the route. Must be present in the railroads file.")
    parser.add_argument("--board-state-file", default="board-state.csv",
            help=("CSV file containing the board state. Semi-colon is the column separator. "
                  "The columns are: coord; tile_id; orientation"))
    parser.add_argument("--railroads-file", default="railroads.csv",
            help=("CSV file containing the board state. Semi-colon is the column separator. "
                  "The columns are: name; trains; stations; chicago_station_exit"))
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = parse_args()
    board = boardstate.load(args["board_state_file"])
    railroads = railroads.load(board, args["railroads_file"])
    calc_route(board, railroads, railroads[args["active-railroad"]])