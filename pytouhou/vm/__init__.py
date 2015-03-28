from .anmrunner import ANMRunner
from .msgrunner import MSGRunner
from .eclrunner import ECLMainRunner


class PythonMainRunner:
    def __init__(self, main, game):
        self.main = main
        self.game = game

    def run_iter(self):
        self.main(self.game)


class EnemyRunner:
    def __init__(self, enemy, game, sub):
        self.enemy = enemy
        self.game = game
        self.sub = sub

    def run_iteration(self):
        self.sub(self.enemy, self.game)


def spawn_enemy(game, sub, x=0., y=0., life=1, item=-1, score=0, mirrored=False, random=False):
    instr_type = (2 if mirrored else 0) | (4 if random else 0)
    enemy = game.new_enemy((x, y, 0.), life, instr_type, item, score)
    enemy.process = EnemyRunner(enemy, game, sub)
    enemy.process.run_iteration()
