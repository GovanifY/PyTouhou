//! Interpreter of STD files.

use crate::th06::std::{Stage, Position, Call, Instruction};
use crate::th06::interpolator::{Interpolator1, Interpolator4};
use crate::util::math::{Mat4, perspective, setup_camera};
use std::cell::RefCell;
use std::rc::Rc;

/// Interpreter for Stage.
pub struct StageRunner {
    /// XXX: no pub.
    pub stage: Rc<RefCell<Stage>>,
    frame: u32,

    // TODO: use interpolators.
    position: [f32; 3],
    direction: [f32; 3],

    /// XXX: no pub.
    pub fog_color: [f32; 4],
    /// XXX: no pub.
    pub fog_near: f32,
    /// XXX: no pub.
    pub fog_far: f32,
}

impl StageRunner {
    /// Create a new StageRunner attached to a Stage.
    pub fn new(stage: Rc<RefCell<Stage>>) -> StageRunner {
        StageRunner {
            stage,
            frame: 0,
            position: [0.; 3],
            direction: [0.; 3],
            fog_color: [1.; 4],
            fog_near: 0.,
            fog_far: 1000.,
        }
    }

    /// Advance the simulation one frame.
    pub fn run_frame(&mut self) {
        let stage = self.stage.borrow();

        for Call { time, instr } in stage.script.iter() {
            if *time != self.frame {
                continue;
            }

            println!("{} {:?}", time, instr);

            match *instr {
                Instruction::SetViewpos(x, y, z) => {
                    self.position[0] = x;
                    self.position[1] = y;
                    self.position[2] = z;
                }
                Instruction::SetFog(b, g, r, a, near, far) => {
                    self.fog_color = [r as f32 / 255., g as f32 / 255., b as f32 / 255., a as f32 / 255.];
                    self.fog_near = near;
                    self.fog_far = far;
                }
                Instruction::SetViewpos2(dx, dy, dz) => {
                    self.direction[0] = dx;
                    self.direction[1] = dy;
                    self.direction[2] = dz;
                }
                Instruction::StartInterpolatingViewpos2(frame, _, _) => {
                }
                Instruction::StartInterpolatingFog(frame, _, _) => {
                }
                Instruction::Unknown(_, _, _) => {
                }
            }
        }

        self.frame += 1;
    }

    /// Generate the model-view matrix for the current frame.
    pub fn get_model_view(&self) -> Mat4 {
        let [x, y, z] = self.position;

        let [dx, dy, dz] = self.direction;

        let view = setup_camera(dx, dy, dz);

        let model = Mat4::new([[1., 0., 0., 0.],
                               [0., 1., 0., 0.],
                               [0., 0., 1., 0.],
                               [-x, -y, -z, 1.]]);
        model * view
    }
}
