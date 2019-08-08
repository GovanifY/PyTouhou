//! Module providing an Enemy struct, to be changed by EclRunner.

use crate::th06::anm0::Anm0;
use crate::th06::anm0_vm::{Sprite, AnmRunner};
use crate::th06::interpolator::{Interpolator1, Interpolator2};
use crate::util::prng::Prng;
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::{Rc, Weak};

#[derive(Debug, Clone, Copy)]
struct Position {
    x: f32,
    y: f32,
}

#[derive(Debug, Clone, Copy)]
struct Offset {
    dx: f32,
    dy: f32,
}

impl Position {
    pub fn new(x: f32, y: f32) -> Position {
        Position { x, y }
    }
}

impl Offset {
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

#[derive(Debug, Clone)]
struct Process;

struct Game {
    enemies: Vec<Enemy>,
    prng: Rc<RefCell<Prng>>,
}

/// Common to all elements in game.
struct Element {
    pos: Position,
    removed: bool,
    sprite: Weak<RefCell<Sprite>>,
    anmrunner: AnmRunner,
}

/// The enemy struct, containing everything pertaining to an enemy.
pub struct Enemy {
    // Common to all elements in game.
    pos: Position,
    removed: bool,
    sprite: Rc<RefCell<Sprite>>,
    anmrunner: Rc<RefCell<AnmRunner>>,

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
    low_life_trigger: u32,
    timeout: u32,
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
    options: Vec<Element>,

    // Interpolators.
    interpolator: Option<Interpolator2<f32>>,
    speed_interpolator: Option<Interpolator1<f32>>,

    // Misc stuff, do we need them?
    anm0: Weak<RefCell<Anm0>>,
    process: Rc<RefCell<Process>>,
    game: Weak<RefCell<Game>>,
    prng: Weak<RefCell<Prng>>,
    hitbox_half_size: (f32, f32),
}

impl Enemy {
    /// Sets the animation to the one indexed by index in the current anm0.
    pub fn set_anim(&mut self, index: u8) {
        self.sprite = Rc::new(RefCell::new(Sprite::new()));
        let anm0 = self.anm0.upgrade().unwrap();
        let anmrunner = AnmRunner::new(&*anm0.borrow(), index, self.sprite.clone(), self.prng.clone(), 0);
        self.anmrunner = Rc::new(RefCell::new(anmrunner));
    }
}
