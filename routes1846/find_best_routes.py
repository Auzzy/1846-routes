import itertools
import logging

from routes1846.board import Board
from routes1846.route import Route
from routes1846.cell import CHICAGO_CELL

LOG = logging.getLogger(__name__)


def _get_train_sets(route_by_train):
    train_sets = []
    for train_count in range(1, len(route_by_train) + 1):
        train_sets += [list(train_set) for train_set in itertools.combinations(route_by_train.keys(), train_count)]
    return train_sets

def _find_best_routes_by_train(route_by_train, railroad):
    if len(route_by_train) == 1:
        run_routes = [{train: (route, value)} for train, routes in route_by_train.items() for route, value in routes.items()]
    else:
        run_routes = []
        for train_set in _get_train_sets(route_by_train):
            route_sets = itertools.product(*[route_by_train[train].keys() for train in train_set])

            for route_set in route_sets:
                for route1, route2 in itertools.combinations(route_set, 2):
                    if route1.overlap(route2):
                        break
                else:
                    run_routes.append({train: (route, route_by_train[train][route]) for train, route in zip(train_set, route_set)})

    LOG.debug("Found %d route sets.", len(run_routes))
    for run_route in run_routes:
        LOG.debug(str(run_route))

    return max(run_routes, key=lambda run_route: sum(value for route, value in run_route.values())) if run_routes else {}

def _get_subroutes(routes, stations):
    subroutes = [route.subroutes(station.cell) for station in stations for route in routes]
    return set(itertools.chain.from_iterable([subroute for subroute in subroutes if subroute]))

def _find_connected_cities(board, railroad, cell, dist):
    tiles = itertools.chain.from_iterable(_walk_routes(board, railroad, None, cell, dist))
    return {tile.cell for tile in tiles if tile.is_city} - {cell}

def _walk_routes(board, railroad, enter_from, cell, length, visited=None):
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

    neighbors = tile.paths(enter_from, railroad)

    routes = []
    for neighbor in neighbors:
        neighbor_paths = _walk_routes(board, railroad, cell, neighbor, remaining_cities, visited + [tile])
        routes += [Route.single(tile).merge(neighbor_path) for neighbor_path in neighbor_paths if neighbor_path]

    if not routes and tile.is_city:
        routes.append(Route.single(tile))

    unique_routes = tuple(set(routes))
    
    route_str = "\n- ".join([str(route) for route in unique_routes])
    LOG.debug("Found %d routes starting at %s:\n- %s", len(unique_routes), cell, route_str)

    return unique_routes


def _find_routes_from_cell(board, railroad, cell, train):
    tile = board.get_space(cell)
    if not tile.is_city:
        raise Exception("How is your station not in a city? {}".format(cell))

    routes = _walk_routes(board, railroad, None, cell, train.visit)

    # A route must connect at least 2 cities.
    routes = [route for route in routes if len(route.cities) >= 2]

    LOG.debug("Found %d routes starting at %d.", len(routes), cell)
    return routes

def _find_connected_routes(board, railroad, station, train):
    LOG.debug("Finding connected cities.")
    connected_cities = _find_connected_cities(board, railroad, station.cell, train.visit - 1)
    LOG.debug("Connected cities: %s", ", ".join([str(cell) for cell in connected_cities]))

    LOG.debug("Finding routes starting from connected cities.")
    connected_routes = set()
    for cell in connected_cities:
        for path in _find_routes_from_cell(board, railroad, cell, train):
            if station.cell == CHICAGO_CELL:
                chicago = board.get_space(CHICAGO_CELL)
                exit_cell = chicago.get_station_exit_cell(station)
                if path.contains_cell(CHICAGO_CELL) and path.contains_cell(exit_cell):
                    connected_routes.add(path)
            elif path.contains_cell(station.cell):
                connected_routes.add(path)
    LOG.debug("Found %d routes from connected cities.", len(connected_routes))
    return connected_routes

def _find_all_routes(board, railroad):
    LOG.info("Finding all possible routes for each train from %s's stations.", railroad.name)

    stations = board.stations(railroad.name)

    routes = {}
    for train in railroad.trains:
        routes[train] = set()
        for station in stations:
            LOG.debug("Finding routes starting at station at %s.", station.cell)
            routes[train].update(_find_routes_from_cell(board, railroad, station.cell, train))

            LOG.debug("Finding routes which pass through station at %s.", station.cell)
            connected_paths = _find_connected_routes(board, railroad, station, train)
            routes[train].update(connected_paths)

        LOG.debug("Add subroutes")
        routes[train].update(_get_subroutes(routes[train], stations))

    LOG.info("Found %d routes.", len(routes))

    return routes

def _detect_phase(railroads):
    return max([train.phase for railroad in railroads.values() for train in railroad.trains])

def find_best_routes(board, railroads, active_railroad):
    LOG.info("Finding the best route for %s.", active_railroad.name)
    
    routes = _find_all_routes(board, active_railroad)

    phase = _detect_phase(railroads)

    LOG.info("Calculating route values.")
    route_value_by_train = {}
    for train in routes:
        route_value_by_train[train] = {route: route.value(train, phase) for route in routes[train]}

    return _find_best_routes_by_train(route_value_by_train, active_railroad)
