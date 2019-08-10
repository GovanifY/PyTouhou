//! Module providing an Enemy struct, to be changed by EclRunner.

use crate::th06::anm0::Anm0;
use crate::th06::anm0_vm::{Sprite, AnmRunner};
use crate::th06::interpolator::{Interpolator1, Interpolator2};
use crate::util::prng::Prng;
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::{Rc, Weak};

/// The 2D position of an object in the game.
#[derive(Debug, Clone, Copy, Default)]
pub struct Position {
    x: f32,
    y: f32,
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
}

impl Game {
    /// Create said god struct.
    pub fn new(prng: Rc<RefCell<Prng>>) -> Game {
        Game {
            enemies: Vec::new(),
            anmrunners: Vec::new(),
            prng,
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
    pub fn get_sprites(&self) -> Vec<Rc<RefCell<Sprite>>> {
        let mut sprites = vec![];
        for anmrunner in self.anmrunners.iter() {
            let anmrunner = anmrunner.borrow();
            let sprite = anmrunner.get_sprite();
            sprites.push(sprite);
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

/// The enemy struct, containing everything pertaining to an enemy.
#[derive(Default)]
pub struct Enemy {
    // Common to all elements in game.
    pos: Position,
    removed: bool,
    anmrunner: Weak<RefCell<AnmRunner>>,

    // Specific to enemy.
    // Floats.
    z: f32,
    angle: f32,
    speed: f32,
    rotation_speed: f32,
    acceleration: f32,

    // Ints.
    type_: u32,
    bonus_dropped: u32,
    die_score: u32,
    frame: u32,
    life: u32,
    death_flags: u32,
    current_laser_id: u32,
    low_life_trigger: Option<u32>,
    timeout: Option<u32>,
    remaining_lives: u32,
    bullet_launch_interval: u32,
    bullet_launch_timer: u32,
    death_anim: u32,
    direction: u32,
    update_mode: u32,

    // Bools.
    visible: bool,
    was_visible: bool,
    touchable: bool,
    collidable: bool,
    damageable: bool,
    boss: bool,
    automatic_orientation: bool,
    delay_attack: bool,

    // Tuples.
    difficulty_coeffs: (f32, f32, u32, u32, u32, u32),
    extended_bullet_attributes: Option<(u32, u32, u32, u32, f32, f32, f32, f32)>,
    bullet_attributes: Option<(i16, i16, u32, u32, u32, f32, f32, f32, f32, u32)>,
    bullet_launch_offset: Offset,
    movement_dependant_sprites: Option<(f32, f32, f32, f32)>,
    screen_box: Option<(f32, f32, f32, f32)>,

    // Callbacks.
    death_callback: Option<Callback>,
    boss_callback: Option<Callback>,
    low_life_callback: Option<Callback>,
    timeout_callback: Option<Callback>,

    // Laser.
    laser_by_id: HashMap<u32, Laser>,

    // Options.
    // TODO: actually a 8 element array.
    options: Vec<Element>,

    // Interpolators.
    interpolator: Option<Interpolator2<f32>>,
    speed_interpolator: Option<Interpolator1<f32>>,

    // Misc stuff, do we need them?
    anm0: Weak<RefCell<Anm0>>,
    process: Rc<RefCell<Process>>,
    game: Weak<RefCell<Game>>,
    prng: Weak<RefCell<Prng>>,
    hitbox_half_size: [f32; 2],
}

impl Enemy {
    /// Create a new enemy.
    pub fn new(pos: Position, life: i32, bonus_dropped: u32, die_score: u32, anm0: Weak<RefCell<Anm0>>, game: Weak<RefCell<Game>>) -> Enemy {
        Enemy {
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
            difficulty_coeffs: (-0.5, 0.5, 0, 0, 0, 0),
            ..Default::default()
        }
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

    /// Sets the hitbox around the enemy.
    pub fn set_hitbox(&mut self, width: f32, height: f32) {
        self.hitbox_half_size = [width, height];
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
        let game = Game::new(prng);
        let game = Rc::new(RefCell::new(game));
        let mut enemy = Enemy::new(Position::new(0., 0.), 500, 0, 640, Rc::downgrade(&anm0), Rc::downgrade(&game));
        assert!(enemy.anmrunner.upgrade().is_none());
        enemy.set_anim(0);
        assert!(enemy.anmrunner.upgrade().is_some());
    }
}
