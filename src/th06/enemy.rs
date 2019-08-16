//! Module providing an Enemy struct, to be changed by EclRunner.

use crate::th06::anm0::Anm0;
use crate::th06::anm0_vm::{Sprite, AnmRunner};
use crate::th06::ecl::Rank;
use crate::th06::interpolator::{Interpolator1, Interpolator2};
use crate::util::prng::Prng;
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::{Rc, Weak};

/// The 2D position of an object in the game.
#[derive(Debug, Clone, Copy, Default)]
pub struct Position {
    pub(crate) x: f32,
    pub(crate) y: f32,
}

/// An offset which can be added to a Position.
#[derive(Debug, Clone, Copy, Default)]
pub struct Offset {
    dx: f32,
    dy: f32,
}

impl Position {
    /// Create said position.
    pub fn new(x: f32, y: f32) -> Position {
        Position { x, y }
    }
}

impl Offset {
    /// Create said offset.
    pub fn new(dx: f32, dy: f32) -> Offset {
        Offset { dx, dy }
    }
}

impl std::ops::Add<Offset> for Position {
    type Output = Position;
    fn add(self, offset: Offset) -> Position {
        Position {
            x: self.x + offset.dx,
            y: self.y + offset.dy,
        }
    }
}

#[derive(Debug, Clone)]
struct Callback;

#[derive(Debug, Clone)]
struct Laser;

#[derive(Debug, Clone, Default)]
struct Process;

/// God struct of our game.
pub struct Game {
    enemies: Vec<Rc<RefCell<Enemy>>>,
    anmrunners: Vec<Rc<RefCell<AnmRunner>>>,
    prng: Rc<RefCell<Prng>>,
    rank: Rank,
    difficulty: i32,
}

impl Game {
    /// Create said god struct.
    pub fn new(prng: Rc<RefCell<Prng>>, rank: Rank) -> Game {
        Game {
            enemies: Vec::new(),
            anmrunners: Vec::new(),
            prng,
            rank,
            difficulty: 0,
        }
    }

    /// Run the simulation for a single frame.
    pub fn run_frame(&mut self) {
        /*
        for eclrunner in self.eclrunners {
            eclrunner.run_frame();
        }
        */

        for anmrunner in self.anmrunners.iter() {
            let mut anmrunner = anmrunner.borrow_mut();
            anmrunner.run_frame();
        }
    }

    /// Returns a list of all sprites currently being displayed on screen.
    pub fn get_sprites(&self) -> Vec<(f32, f32, f32, Rc<RefCell<Sprite>>)> {
        let mut sprites = vec![];
        for enemy in self.enemies.iter() {
            let enemy = enemy.borrow();
            let anmrunner = enemy.anmrunner.upgrade().unwrap();
            let anmrunner = anmrunner.borrow();
            let sprite = anmrunner.get_sprite();
            sprites.push((enemy.pos.x, enemy.pos.y, enemy.z, sprite));
        }
        sprites
    }
}

/// Common to all elements in game.
struct Element {
    pos: Position,
    removed: bool,
    anmrunner: AnmRunner,
}

#[derive(PartialEq)]
pub(crate) struct DifficultyCoeffs {
    pub(crate) speed_a: f32,
    pub(crate) speed_b: f32,
    pub(crate) nb_a: u16,
    pub(crate) nb_b: u16,
    pub(crate) shots_a: u16,
    pub(crate) shots_b: u16,
}

impl Default for DifficultyCoeffs {
    fn default() -> DifficultyCoeffs {
        DifficultyCoeffs {
            speed_a: -0.5,
            speed_b: 0.5,
            nb_a: 0,
            nb_b: 0,
            shots_a: 0,
            shots_b: 0,
        }
    }
}

#[derive(PartialEq)]
pub(crate) enum Direction {
    Left,
    Center,
    Right,
}

impl Default for Direction {
    fn default() -> Direction {
        Direction::Center
    }
}

/// The enemy struct, containing everything pertaining to an enemy.
#[derive(Default)]
pub struct Enemy {
    // Common to all elements in game.
    pub(crate) pos: Position,
    pub(crate) removed: bool,
    pub(crate) anmrunner: Weak<RefCell<AnmRunner>>,

    // Specific to enemy.
    // Floats.
    pub(crate) z: f32,
    pub(crate) angle: f32,
    pub(crate) speed: f32,
    pub(crate) rotation_speed: f32,
    pub(crate) acceleration: f32,

    // Ints.
    pub(crate) type_: u32,
    pub(crate) bonus_dropped: u32,
    pub(crate) die_score: u32,
    /// XXX
    pub frame: u32,
    pub(crate) life: u32,
    pub(crate) death_flags: u32,
    pub(crate) current_laser_id: u32,
    pub(crate) low_life_trigger: Option<u32>,
    pub(crate) timeout: Option<u32>,
    pub(crate) remaining_lives: u32,
    pub(crate) bullet_launch_interval: u32,
    pub(crate) bullet_launch_timer: u32,
    pub(crate) death_anim: i32,
    pub(crate) direction: Direction,
    pub(crate) update_mode: u32,

    // Bools.
    pub(crate) visible: bool,
    pub(crate) was_visible: bool,
    pub(crate) touchable: bool,
    pub(crate) collidable: bool,
    pub(crate) damageable: bool,
    pub(crate) boss: bool,
    pub(crate) automatic_orientation: bool,
    pub(crate) delay_attack: bool,

    // Tuples.
    pub(crate) difficulty_coeffs: DifficultyCoeffs,
    pub(crate) extended_bullet_attributes: Option<(u32, u32, u32, u32, f32, f32, f32, f32)>,
    pub(crate) bullet_attributes: Option<(i16, i16, u32, u32, u32, f32, f32, f32, f32, u32)>,
    pub(crate) bullet_launch_offset: Offset,
    pub(crate) movement_dependant_sprites: Option<(u8, u8, u8, u8)>,
    pub(crate) screen_box: Option<(f32, f32, f32, f32)>,

    // Callbacks.
    death_callback: Option<Callback>,
    boss_callback: Option<Callback>,
    low_life_callback: Option<Callback>,
    timeout_callback: Option<Callback>,

    // Laser.
    pub(crate) laser_by_id: HashMap<u32, Laser>,

    // Options.
    // TODO: actually a 8 element array.
    options: Vec<Element>,

    // Interpolators.
    pub(crate) interpolator: Option<Interpolator2<f32>>,
    pub(crate) speed_interpolator: Option<Interpolator1<f32>>,

    // Misc stuff, do we need them?
    pub(crate) anm0: Weak<RefCell<Anm0>>,
    process: Rc<RefCell<Process>>,
    pub(crate) game: Weak<RefCell<Game>>,
    pub(crate) prng: Weak<RefCell<Prng>>,
    pub(crate) hitbox_half_size: [f32; 2],
}

impl Enemy {
    /// Create a new enemy.
    pub fn new(pos: Position, life: i32, bonus_dropped: u32, die_score: u32, anm0: Weak<RefCell<Anm0>>, game: Weak<RefCell<Game>>) -> Rc<RefCell<Enemy>> {
        let game_rc = game.upgrade().unwrap();
        let enemy = Enemy {
            pos,
            anm0,
            game,
            visible: true,
            bonus_dropped,
            die_score,
            life: if life < 0 { 1 } else { life as u32 },
            touchable: true,
            collidable: true,
            damageable: true,
            ..Default::default()
        };
        let enemy = Rc::new(RefCell::new(enemy));
        game_rc.borrow_mut().enemies.push(enemy.clone());
        enemy
    }

    /// Sets the animation to the one indexed by index in the current anm0.
    pub fn set_anim(&mut self, index: u8) {
        let anm0 = self.anm0.upgrade().unwrap();
        let game = self.game.upgrade().unwrap();
        let sprite = Rc::new(RefCell::new(Sprite::new()));
        let anmrunner = AnmRunner::new(&*anm0.borrow(), index, sprite, self.prng.clone(), 0);
        let anmrunner = Rc::new(RefCell::new(anmrunner));
        self.anmrunner = Rc::downgrade(&anmrunner);
        (*game.borrow_mut()).anmrunners.push(anmrunner);
    }

    /// Sets the current position of the enemy.
    pub fn set_pos(&mut self, x: f32, y: f32, z: f32) {
        self.pos.x = x;
        self.pos.y = y;
        self.z = z;
    }

    /// Sets the hitbox around the enemy.
    pub fn set_hitbox(&mut self, width: f32, height: f32) {
        self.hitbox_half_size = [width / 2., height / 2.];
    }

    /// Run all interpolators and such, and update internal variables once per
    /// frame.
    pub fn update(&mut self) {
        let Position { mut x, mut y } = self.pos;

        let speed = if self.update_mode == 1 {
            let mut speed = 0.;
            if let Some(interpolator) = &self.interpolator {
                let values = interpolator.values(self.frame as u16);
                x = values[0];
                y = values[1];
            }
            if let Some(interpolator) = &self.speed_interpolator {
                let values = interpolator.values(self.frame as u16);
                speed = values[0];
            }
            speed
        } else {
            let speed = self.speed;
            self.speed += self.acceleration;
            self.angle += self.rotation_speed;
            speed
        };

        let dx = self.angle.cos() * speed;
        let dy = self.angle.sin() * speed;
        if self.type_ & 2 != 0 {
            x -= dx;
        } else {
            x += dx;
        }
        y += dy;

        if let Some((end_left, end_right, left, right)) = self.movement_dependant_sprites {
            if x < self.pos.x && self.direction != Direction::Left {
                self.set_anim(left);
                self.direction = Direction::Left;
            } else if x > self.pos.x && self.direction != Direction::Right {
                self.set_anim(right);
                self.direction = Direction::Right;
            } else if x == self.pos.x && self.direction != Direction::Center {
                let anim = if self.direction == Direction::Left {
                    end_left
                } else {
                    end_right
                };
                self.set_anim(anim);
                self.direction = Direction::Center;
            }
        }

        self.pos = Position { x, y };

        self.frame += 1;
    }

    pub(crate) fn get_rank(&self) -> Rank {
        let game = self.game.upgrade().unwrap();
        let game = game.borrow();
        game.rank
    }

    pub(crate) fn get_difficulty(&self) -> i32 {
        let game = self.game.upgrade().unwrap();
        let game = game.borrow();
        game.difficulty
    }
}

trait Renderable {
    fn get_sprites(&self) -> Vec<Rc<RefCell<Sprite>>>;
}

impl Renderable for Enemy {
    fn get_sprites(&self) -> Vec<Rc<RefCell<Sprite>>> {
        let anmrunner = self.anmrunner.upgrade().unwrap();
        let anmrunner = anmrunner.borrow();
        vec![anmrunner.get_sprite()]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{self, Read};
    use std::fs::File;

    #[test]
    fn enemy() {
        let file = File::open("EoSD/ST/stg1enm.anm").unwrap();
        let mut file = io::BufReader::new(file);
        let mut buf = vec![];
        file.read_to_end(&mut buf).unwrap();
        let anm0 = Anm0::from_slice(&buf).unwrap();
        let anm0 = Rc::new(RefCell::new(anm0));
        let prng = Rc::new(RefCell::new(Prng::new(0)));
        let game = Game::new(prng, Rank::Easy);
        let game = Rc::new(RefCell::new(game));
        let enemy = Enemy::new(Position::new(0., 0.), 500, 0, 640, Rc::downgrade(&anm0), Rc::downgrade(&game));
        let mut enemy = enemy.borrow_mut();
        assert!(enemy.anmrunner.upgrade().is_none());
        enemy.set_anim(0);
        assert!(enemy.anmrunner.upgrade().is_some());
    }
}
