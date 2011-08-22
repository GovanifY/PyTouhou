class GameState(object):
    __slots__ = ('players', 'rank', 'difficulty', 'frame', 'stage', 'boss')
    def __init__(self, players, stage, rank, difficulty):
        self.stage = stage
        self.players = players
        self.rank = rank
        self.difficulty = difficulty
        self.boss = None
        self.frame = 0
