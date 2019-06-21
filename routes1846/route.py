import heapq

from routes1846.boardtile import EastTerminalCity, WestTerminalCity

class Route(object):
    @staticmethod
    def create(path):
        return Route(tuple(path))

    @staticmethod
    def empty():
        return Route(tuple())

    @staticmethod
    def single(tile):
        return Route.create((tile, ))

    def __init__(self, path):
        self._path = tuple(path)
        self._edges = [{path[k-1], path[k]} for k in range(1, len(path))]

    def merge(self, route):
        return Route.create(self._path + route._path)

    def _best_cities(self, train, route_city_values, station_cities):
        best_station_city = max(station_cities.items(), key=lambda tile_and_value: tile_and_value[1])

        city_values = route_city_values.copy()
        del city_values[best_station_city[0]]

        best_cities = dict(heapq.nlargest(train.collect - 1, city_values.items(), key=lambda city_item: city_item[1]))
        best_cities.update(dict([best_station_city]))

        return best_cities, sum(best_cities.values())

    def value(self, board, train, railroad, phase):
        route_city_values = {tile: tile.value(railroad, phase) for tile in self if tile.is_city}
        station_cells = {station.cell for station in board.stations(railroad.name)}
        station_cities = {tile: value for tile, value in route_city_values.items() if tile.cell in station_cells}

        best_cities, base_route_value = self._best_cities(train, route_city_values, station_cities)

        # Check for east west bonus.
        ends = [self._path[0], self._path[-1]]
        east_to_west = all(isinstance(tile, (EastTerminalCity, WestTerminalCity)) for tile in ends) and type(ends[0]) != type(ends[1])
        if east_to_west:
            # There is an east-west route. Confirm that those terminal cities
            # plus their bonuses is the highest value route.
            route_city_values_with_bonus = route_city_values.copy()
            route_city_values_with_bonus.update({end: end.value(railroad, phase, east_to_west) for end in ends})

            best_cities_with_bonus, base_route_value_with_bonus = self._best_cities(train, route_city_values_with_bonus, station_cities)

            return best_cities_with_bonus if base_route_value_with_bonus >= base_route_value else best_cities
        else:
            return best_cities

    def overlap(self, other):
        for edge in self._edges:
            if edge in other._edges:
                return True
        return False

    def subroutes(self, start):
        if not self.contains_cell(start):
            return Route.empty()

        start_index = [index for index, tile in enumerate(self._path) if tile.cell == start][0]
        backwards_subroutes = {Route.create(self._path[index:start_index]) for index in range(start_index - 1, -1, -1)}
        forwards_subroutes = {Route.create(self._path[start_index:index]) for index in range(start_index + 1, len(self._path))}
        subroutes = backwards_subroutes.union(forwards_subroutes)
        return [subroute for subroute in subroutes if len(subroute.cities) >= 2]

    def contains_cell(self, cell):
        return cell in [tile.cell for tile in self]

    @property
    def cities(self):
        return [tile for tile in self._path if tile.is_city]

    def __iter__(self):
        return iter(self._path)

    def __bool__(self):
        return bool(self._path)
    
    def __len__(self):
        return len(self._path)

    def __hash__(self):
        return hash(tuple(set(self._path)))

    def __eq__(self, other):
        return isinstance(other, Route) and set(other._path) == set(self._path)

    def __str__(self):
        return ", ".join([str(tile.cell) for tile in self])

    def run(self, board, train, railroad, phase):
        visited_cities = self.value(board, train, railroad, phase)
        return _RunRoute(self, visited_cities, train)

class _RunRoute(object):
    def __init__(self, route, visited_city_values, train):
        self._route = route
        self.city_values = dict.fromkeys(route.cities, 0)
        self.city_values.update(visited_city_values)
        self.value = sum(self.city_values.values())
        self.train = train

        self._mail_contract = False

    def overlap(self, other):
        return self._route.overlap(other._route)

    def add_mail_contract(self):
        if not self._mail_contract:
            self.value += len(self._route.cities) * 10

            self._mail_contract = True

    @property
    def cities(self):
        return self._route.cities

    @property
    def visited_cities(self):
        return [city for city in self.cities if self.city_values[city] > 0]

    def __str__(self):
        return str(self._route)

    def __iter__(self):
        return iter(self._route)