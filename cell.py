MIN_ROW = "A"
MAX_ROW = "K"
MIN_COL = 1
MAX_COL = 23

class Cell(object):
    @staticmethod
    def from_coord(coord):
        row, col = coord[0], int(coord[1:])
        return Cell(row, col)

    def __init__(self, row, col):
        self._row = row
        self._col = col

    @property
    def neighbors(self):
        return {
            1: Cell(chr(ord(self._row) + 1), self._col - 1),
            2: Cell(self._row, self._col - 2),
            3: Cell(chr(ord(self._row) - 1), self._col - 1),
            4: Cell(chr(ord(self._row) - 1), self._col + 1),
            5: Cell(self._row, self._col + 2),
            6: Cell(chr(ord(self._row) + 1), self._col + 1)
        }

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, Cell):
            return False
        return str(self) == str(other)

    def __str__(self):
        return "{}{}".format(self._row, self._col)

    def __repr__(self):
        return str(self)