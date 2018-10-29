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

    def value(self, train, phase):
        edges = [self._path[0], self._path[-1]]
        east_to_west = not bool({EastTerminalCity, WestTerminalCity} - {type(tile) for tile in edges})
        if east_to_west:
            with_bonus = sum(heapq.nlargest(train.collect - 2, [tile.value(phase) for tile in self._path[1:-1]])) + sum([edge.value(phase, east_to_west) for edge in edges])
            without_bonus = sum(heapq.nlargest(train.collect, [tile.value(phase) for tile in self]))
            return max((with_bonus, without_bonus))
        else:
            return sum(heapq.nlargest(train.collect, [tile.value(phase) for tile in self]))

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