from pytouhou.utils.random import Random

class GameState(object):
    __slots__ = ('players', 'rank', 'difficulty', 'frame', 'stage', 'boss', 'prng')
    def __init__(self, players, stage, rank, difficulty):
        self.stage = stage
        self.players = players
        self.rank = rank
        self.difficulty = difficulty
        self.boss = None
        self.prng = Random()
        self.frame = 0
