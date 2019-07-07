//! Animation runner.

use crate::th06::anm0::{
    Script,
    Anm0,
    Call,
    Instruction,
};
use crate::th06::interpolator::{Interpolator1, Interpolator2, Interpolator3, Formula};
use std::cell::RefCell;
use std::rc::Rc;

/// Base visual element.
#[derive(Debug, Clone, Default)]
pub struct Sprite {
    blendfunc: u32,
    frame: u16,

    width_override: f32,
    height_override: f32,
    angle: f32,

    removed: bool,
    changed: bool,
    visible: bool,
    force_rotation: bool,
    automatic_orientation: bool,
    allow_dest_offset: bool,
    mirrored: bool,
    corner_relative_placement: bool,

    scale_interpolator: Option<Interpolator2<f32>>,
    fade_interpolator: Option<Interpolator1<f32>>, // XXX: should be u8!
    offset_interpolator: Option<Interpolator3<f32>>,
    rotation_interpolator: Option<Interpolator3<f32>>,
    color_interpolator: Option<Interpolator3<f32>>, // XXX: should be u8!

    anm: Option<Anm0>,

    dest_offset: [f32; 3],
    texcoords: [f32; 4],
    texoffsets: [f32; 2],
    rescale: [f32; 2],
    scale_speed: [f32; 2],
    rotations_3d: [f32; 3],
    rotations_speed_3d: [f32; 3],
    color: [u8; 4],
}

impl Sprite {
    /// Create a new sprite.
    pub fn new(width_override: f32, height_override: f32) -> Sprite {
        Sprite {
            width_override,
            height_override,
            changed: true,
            visible: true,
            rescale: [1., 1.],
            color: [255, 255, 255, 255],
            ..Default::default()
        }
    }

    /// Update sprite values from the interpolators.
    pub fn update(&mut self) {
        self.frame += 1;

        let [sax, say, saz] = self.rotations_speed_3d;
        if sax != 0. || say != 0. || saz != 0. {
            let [ax, ay, az] = self.rotations_3d;
            self.rotations_3d = [ax + sax, ay + say, az + saz];
            self.changed = true;
        } else if let Some(ref interpolator) = self.rotation_interpolator {
            self.rotations_3d = interpolator.values(self.frame);
            self.changed = true;
        }

        let [rsx, rsy] = self.scale_speed;
        if rsx != 0. || rsy != 0. {
            let [rx, ry] = self.rescale;
            self.rescale = [rx + rsx, ry + rsy];
            self.changed = true;
        }

        if let Some(ref interpolator) = self.fade_interpolator {
            self.color[3] = interpolator.values(self.frame)[0] as u8;
            self.changed = true;
        }

        if let Some(ref interpolator) = self.scale_interpolator {
            self.rescale = interpolator.values(self.frame);
            self.changed = true;
        }

        if let Some(ref interpolator) = self.offset_interpolator {
            self.dest_offset = interpolator.values(self.frame);
            self.changed = true;
        }

        if let Some(ref interpolator) = self.color_interpolator {
            let color = interpolator.values(self.frame);
            // TODO: this can probably be made to look nicer.
            self.color[0] = color[0] as u8;
            self.color[1] = color[1] as u8;
            self.color[2] = color[2] as u8;
            self.changed = true;
        }
    }
}

/// Interpreter for `Anm0` instructions to update a `Sprite`.
pub struct AnmRunner {
    anm: Anm0,
    sprite: Rc<RefCell<Sprite>>,
    running: bool,
    sprite_index_offset: u32,
    script: Script,
    instruction_pointer: usize,
    frame: u16,
    waiting: bool,
    variables: ([i32; 4], [f32; 4], [i32; 4]),
    timeout: Option<u16>,
}

impl AnmRunner {
    /// Create a new `AnmRunner`.
    pub fn new(anm: &Anm0, script_id: u8, sprite: Rc<RefCell<Sprite>>, sprite_index_offset: u32) -> AnmRunner {
        let mut runner = AnmRunner {
            anm: anm.clone(),
            sprite: sprite,
            running: true,
            waiting: false,

            script: anm.scripts[&script_id].clone(),
            frame: 0,
            timeout: None,
            instruction_pointer: 0,
            variables: ([0,  0,  0,  0 ],
                        [0., 0., 0., 0.],
                        [0,  0,  0,  0 ]),

            sprite_index_offset: sprite_index_offset,
        };
        runner.run_frame();
        runner.sprite_index_offset = 0;
        runner
    }

    /// Trigger an interrupt.
    pub fn interrupt(&mut self, interrupt: i32) -> bool {
        let mut new_ip = self.script.interrupts.get(&interrupt);
        if new_ip.is_none() {
            new_ip = self.script.interrupts.get(&-1);
        }
        let new_ip = if let Some(new_ip) = new_ip {
            *new_ip as usize
        } else {
            return false;
        };
        self.instruction_pointer = new_ip;
        let Call { time: frame, instr: _ } = &self.script.instructions[self.instruction_pointer];
        self.frame = *frame;
        self.waiting = false;
        self.sprite.borrow_mut().visible = true;
        true
    }

    /// Advance the Anm of a single frame.
    pub fn run_frame(&mut self) -> bool {
        if !self.running {
            return false;
        }

        while self.running && !self.waiting {
            let Call { time: frame, instr } = self.script.instructions[self.instruction_pointer];
            let frame = frame.clone();

            if frame > self.frame {
                break;
            } else {
                self.instruction_pointer += 1;
            }

            if frame == self.frame {
                self.run_instruction(instr);
                self.sprite.borrow_mut().changed = true;
            }
        }

        if !self.waiting {
            self.frame += 1;
        } else if let Some(timeout) = self.timeout {
            if timeout == self.sprite.borrow().frame { // TODO: check if it’s happening at the correct frame.
                self.waiting = false;
            }
        }

        self.sprite.borrow_mut().update();

        self.running
    }

    fn run_instruction(&mut self, instruction: Instruction) {
        let mut sprite = self.sprite.borrow_mut();
        match instruction {
            Instruction::Delete() => {
                sprite.removed = true;
                self.running = false;
            }
            Instruction::LoadSprite(sprite_index) => {
                sprite.anm = Some(self.anm.clone());
                let texcoords = &self.anm.sprites[(sprite_index + self.sprite_index_offset) as usize];
                sprite.texcoords = [texcoords.x, texcoords.y, texcoords.width, texcoords.height];
            }
            Instruction::SetScale(sx, sy) => {
                sprite.rescale = [sx, sy];
            }
            Instruction::SetAlpha(alpha) => {
                // TODO: check this modulo.
                sprite.color[3] = (alpha % 256) as u8;
            }
            Instruction::SetColor(b, g, r) => {
                if sprite.fade_interpolator.is_none() {
                    sprite.color[0] = r;
                    sprite.color[1] = g;
                    sprite.color[2] = b;
                }
            }
            Instruction::Jump(pointer) => {
                // TODO: is that really how it works?
                self.instruction_pointer = pointer as usize;
                self.frame = self.script.instructions[pointer as usize].time;
            }
            Instruction::ToggleMirrored() => {
                sprite.mirrored = !sprite.mirrored;
            }
            Instruction::SetRotations3d(rx, ry, rz) => {
                sprite.rotations_3d = [rx, ry, rz];
            }
            Instruction::SetRotationsSpeed3d(srx, sry, srz) => {
                sprite.rotations_speed_3d = [srx, sry, srz];
            }
            Instruction::SetScaleSpeed(ssx, ssy) => {
                sprite.scale_speed = [ssx, ssy];
            }
            Instruction::Fade(new_alpha, duration) => {
                sprite.fade_interpolator = Some(Interpolator1::new([sprite.color[3] as f32], sprite.frame, [new_alpha as f32], sprite.frame + duration as u16, Formula::Linear));
            }
            Instruction::SetBlendmodeAlphablend() => {
                sprite.blendfunc = 1;
            }
            Instruction::SetBlendmodeAdd() => {
                sprite.blendfunc = 0;
            }
            Instruction::KeepStill() => {
                self.running = false;
            }
            Instruction::LoadRandomSprite(min_index, amplitude) => {
                let sprite_index = min_index; // XXX: + randrange(amplitude);

                // TODO: refactor that with Instruction::LoadSprite.
                sprite.anm = Some(self.anm.clone());
                let texcoords = &self.anm.sprites[(sprite_index + self.sprite_index_offset) as usize];
                sprite.texcoords = [texcoords.x, texcoords.y, texcoords.width, texcoords.height];
            }
            Instruction::Move(x, y, z) => {
                sprite.dest_offset = [x, y, z];
            }
            Instruction::MoveToLinear(x, y, z, duration) => {
                sprite.offset_interpolator = Some(Interpolator3::new(sprite.dest_offset, sprite.frame, [x, y, z], sprite.frame + duration as u16, Formula::Linear));
            }
            Instruction::MoveToDecel(x, y, z, duration) => {
                sprite.offset_interpolator = Some(Interpolator3::new(sprite.dest_offset, sprite.frame, [x, y, z], sprite.frame + duration as u16, Formula::InvertPower2));
            }
            Instruction::MoveToAccel(x, y, z, duration) => {
                sprite.offset_interpolator = Some(Interpolator3::new(sprite.dest_offset, sprite.frame, [x, y, z], sprite.frame + duration as u16, Formula::Power2));
            }
            Instruction::Wait() => {
                self.waiting = true;
            }
            // There is nothing to do here.
            Instruction::InterruptLabel(_label) => (),
            Instruction::SetCornerRelativePlacement() => {
                sprite.corner_relative_placement = true;
            }
            Instruction::WaitEx() => {
                sprite.visible = false;
                self.waiting = true;
            }
            Instruction::SetAllowOffset(value) => {
                sprite.allow_dest_offset = value == 1
            }
            Instruction::SetAutomaticOrientation(value) => {
                sprite.automatic_orientation = value == 1
            }
            Instruction::ShiftTextureX(dx) => {
                let [tox, toy] = sprite.texoffsets;
                sprite.texoffsets = [tox + dx, toy];
            }
            Instruction::ShiftTextureY(dy) => {
                let [tox, toy] = sprite.texoffsets;
                sprite.texoffsets = [tox, toy + dy];
            }
            Instruction::SetVisible(visible) => {
                sprite.visible = (visible & 1) != 0;
            }
            Instruction::ScaleIn(sx, sy, duration) => {
                sprite.scale_interpolator = Some(Interpolator2::new(sprite.rescale, sprite.frame, [sx, sy], sprite.frame + duration as u16, Formula::Linear));
            }
            Instruction::Todo(_todo) => {
                // TODO.
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{self, Read};
    use std::fs::File;

    #[test]
    fn anm_runner() {
        let file = File::open("/home/linkmauve/games/pc/東方/TH06 ~ The Embodiment of Scarlet Devil/CM/player01.anm").unwrap();
        let mut file = io::BufReader::new(file);
        let mut buf = vec![];
        file.read_to_end(&mut buf).unwrap();
        let anm0 = Anm0::from_slice(&buf).unwrap();
        assert_eq!(anm0.size, (256, 256));
        assert_eq!(anm0.format, 5);
        let sprite = Rc::new(RefCell::new(Sprite::new(0., 0.)));
        let mut anm_runner = AnmRunner::new(&anm0, 1, sprite.clone(), 0);
        for _ in 0..50 {
            anm_runner.run_frame();
        }
    }
}
