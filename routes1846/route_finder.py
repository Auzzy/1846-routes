import itertools
import logging

from routes1846.boardtile import EastTerminalCity
from routes1846.route import Route
from routes1846.cell import CHICAGO_CELL, CHICAGO_CONNECTIONS_CELL

LOG = logging.getLogger(__name__)


class RouteFinder:
    def __init__(self, board):
        self.board = board

    def find_all(self, railroad):
        LOG.info("Finding all possible routes for each train from %s's stations.", railroad.name)

        stations = self.board.stations(railroad.name)

        routes_by_train = {}
        for train in railroad.trains:
            if train not in routes_by_train:
                routes = set()
                for station in stations:
                    LOG.debug("Finding routes starting at station at %s.", station.cell)
                    routes.update(self._from_cell(railroad, station.cell, train))

                    LOG.debug("Finding routes which pass through station at %s.", station.cell)
                    connected_paths = self._connected_routes(railroad, station, train)
                    routes.update(connected_paths)

                LOG.debug("Add subroutes")
                routes.update(self._subroutes(routes, stations))

                LOG.debug("Filtering out invalid routes")
                routes_by_train[train] = self._filter_invalid(routes, railroad)

        LOG.info("Found %d routes.", sum(len(route) for route in routes_by_train.values()))
        for train, routes in routes_by_train.items():
            for route in routes:
                LOG.debug("{}: {}".format(train, str(route)))

        return routes_by_train

    def _connected_routes(self, railroad, station, train):
        LOG.debug("Finding connected cities.")
        connected_cities = self._connected_cities(railroad, station.cell, train.visit - 1)
        LOG.debug("Connected cities: %s", ", ".join([str(cell) for cell in connected_cities]))

        LOG.debug("Finding routes starting from connected cities.")
        connected_routes = set()
        for cell in connected_cities:
            connected_routes.update(self._from_cell(railroad, cell, train))
        LOG.debug("Found %d routes from connected cities.", len(connected_routes))
        return connected_routes

    def _from_cell(self, railroad, cell, train):
        tile = self.board.get_space(cell)
        if not tile.is_city:
            raise Exception("How is your station not in a city? {}".format(cell))

        routes = self._walk_routes(railroad, None, cell, train.visit)

        LOG.debug("Found %d routes starting at %s.", len(routes), cell)
        return routes

    def _walk_routes(self, railroad, enter_from, cell, length, visited=None):
        visited = visited or []

        tile = self.board.get_space(cell)
        if not tile or (enter_from and enter_from not in tile.paths()) or tile in visited:
            return (Route.empty(), )

        if tile.is_city:
            if length - 1 == 0 or (enter_from and not tile.passable(enter_from, railroad)):
                LOG.debug("- %s", ", ".join([str(tile.cell) for tile in visited + [tile]]))
                return (Route.single(tile), )

            remaining_cities = length - 1
        else:
            remaining_cities = length

        neighbors = tile.paths(enter_from, railroad)

        routes = []
        for neighbor in neighbors:
            neighbor_paths = self._walk_routes(railroad, cell, neighbor, remaining_cities, visited + [tile])
            routes += [Route.single(tile).merge(neighbor_path) for neighbor_path in neighbor_paths if neighbor_path]

        if not routes and tile.is_city:
            LOG.debug("- %s", ", ".join([str(tile.cell) for tile in visited + [tile]]))
            routes.append(Route.single(tile))

        return tuple(set(routes))

    def _connected_cities(self, railroad, cell, dist):
        tiles = itertools.chain.from_iterable(self._walk_routes(railroad, None, cell, dist))
        return {tile.cell for tile in tiles if tile.is_city} - {cell}

    def _subroutes(self, routes, stations):
        subroutes = [route.subroutes(station.cell) for station in stations for route in routes]
        return set(itertools.chain.from_iterable([subroute for subroute in subroutes if subroute]))

    def _filter_invalid(self, routes, railroad):
        """
        Given a collection of routes, returns a new set containing only valid routes. Invalid routes removed:
        - contain less than 2 cities, or
        - go through Chicago using an impassable exit
        - only contain Chicago as a station, but don't use the correct exit path

        This fltering after the fact keeps the path finding algorithm simpler. It allows groups of 3 cells to be considered
        (important for the Chicago checks), which would be tricky, since the algorithm operates on pairs of cells (at the
        time of writing).
        """
        chicago_space = self.board.get_space(CHICAGO_CELL)

        chicago_neighbor_cells = [cell for cell in CHICAGO_CELL.neighbors.values() if cell != CHICAGO_CONNECTIONS_CELL]
        stations = self.board.stations(railroad.name)

        # A sieve style filter. If a condition isn't met, iteration continues to the next item. Items meeting all conditions
        # are added to valid_routes at the end of the loop iteration.
        valid_routes = set()
        for route in routes:
            # A route must connect at least 2 cities.
            if len(route.cities) < 2:
                continue

            # A route cannot run from east to east
            if isinstance(route.cities[0], EastTerminalCity) and isinstance(route.cities[-1], EastTerminalCity):
                continue

            # If the route goes through Chicago and isn't [C5, D6], ensure the path it took either contains its station or is unblocked
            if route.contains_cell(CHICAGO_CONNECTIONS_CELL) and len(route.cities) != 2:
                # Finds the subroute which starts at Chicago and is 3 tiles long. That is, it will go [C5, D6, chicago exit]
                all_chicago_subroutes = [subroute for subroute in route.subroutes(CHICAGO_CONNECTIONS_CELL) if len(subroute) == 3]
                chicago_subroute = all_chicago_subroutes[0] if all_chicago_subroutes else None
                for cell in chicago_neighbor_cells:
                    chicago_exit = chicago_subroute and chicago_subroute.contains_cell(cell)
                    if chicago_exit and chicago_space.passable(cell, railroad):
                        break
                else:
                    continue

            # Each route must contain at least 1 station
            stations_on_route = [station for station in stations if route.contains_cell(station.cell)]
            if not stations_on_route:
                continue
            # If the only station is Chicago, the path must be [D6, C5], or exit through the appropriate side.
            elif [CHICAGO_CELL] == [station.cell for station in stations_on_route]:
                exit_cell = self.board.get_space(CHICAGO_CELL).get_station_exit_cell(stations_on_route[0])
                chicago_exit_route = Route.create([chicago_space, self.board.get_space(exit_cell)])
                if not (len(route) == 2 and route.contains_cell(CHICAGO_CONNECTIONS_CELL)) and not route.overlap(chicago_exit_route):
                    continue

            valid_routes.add(route)

        return valid_routes