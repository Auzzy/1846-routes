class Token(object):
    def __init__(self, cell, railroad):
        self.cell = cell
        self.railroad = railroad

class Station(Token):
    pass

class SeaportToken(Token):
    pass

class MeatPackingToken(Token):
    pass