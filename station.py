from cell import Cell

class Station(object):
    @staticmethod
    def from_coord(coord, railroad):
        cell = Cell.from_coord(coord)
        return Station(cell, railroad)

    def __init__(self, cell, railroad):
        self.cell = cell
        self.railroad = railroad