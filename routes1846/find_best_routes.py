import itertools

from routes1846.board import Board
from routes1846.route import Route


def _find_best_routes_by_train(route_by_train, railroad):
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

    neighbors = tile.paths(enter_from, railroad) if enter_from else tile.paths()
    routes = []
    for neighbor in neighbors:
        neighbor_paths = _walk_routes(board, railroad, cell, neighbor, remaining_cities, visited + [tile])
        for neighbor_path in neighbor_paths:
            if neighbor_path:
                routes.append(Route.single(tile).merge(neighbor_path))
    if not routes and tile.is_city:
        routes.append(Route.single(tile))
    return tuple(set(routes))


def _find_routes_from_cell(board, railroad, cell, train):
    tile = board.get_space(cell)
    if not tile.is_city:
        raise Exception("How is your station not in a city? {}".format(cell))

    return _walk_routes(board, railroad, None, cell, train.visit)

def _find_all_routes(board, railroad):
    stations = board.stations(railroad.name)

    routes = {}
    for train in railroad.trains:
        routes[train] = set()
        for station in stations:
            routes[train].update(_find_routes_from_cell(board, railroad, station.cell, train))

            connected_cities = _find_connected_cities(board, railroad, station.cell, train.visit - 1)
            connected_paths = set()
            for cell in connected_cities:
                for path in _find_routes_from_cell(board, railroad, cell, train):
                    if path.contains_cell(station.cell):
                        connected_paths.add(path)

            routes[train].update(connected_paths)

        routes[train].update(_get_subroutes(routes[train], stations))

    return routes

def _detect_phase(railroads):
    return max([train.phase for railroad in railroads.values() for train in railroad.trains])

def find_best_routes(board, railroads, active_railroad):
    routes = _find_all_routes(board, active_railroad)

    phase = _detect_phase(railroads)
    route_value_by_train = {}
    for train in routes:
        route_value_by_train[train] = {route: route.value(train, phase) for route in routes[train]}

    return _find_best_routes_by_train(route_value_by_train, active_railroad)
