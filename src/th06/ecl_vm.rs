//! ECL runner.

use crate::th06::ecl::{Ecl, SubInstruction};
use crate::th06::enemy::Enemy;
use crate::util::prng::Prng;
use std::cell::RefCell;
use std::rc::Rc;

type Variables = ([i32; 4], [f32; 4], [i32; 4]);

/// Interpreter for enemy scripts.
#[derive(Default)]
pub struct EclRunner {
    enemy: Rc<RefCell<Enemy>>,
    ecl: Option<Ecl>,
    sub: u8,
    /// XXX
    pub running: bool,
    /// XXX
    pub frame: i32,
    ip: i32,
    variables: Variables,
    comparison_reg: i8,
    stack: Vec<Variables>,
}

impl EclRunner {
    /// Create a new ECL runner.
    pub fn new(ecl: &Ecl, enemy: Rc<RefCell<Enemy>>, sub: u8) -> EclRunner {
        EclRunner {
            enemy,
            // XXX: no clone.
            ecl: Some(ecl.clone()),
            sub,
            running: true,
            ..Default::default()
        }
    }

    /// Advance the ECL of a single frame.
    pub fn run_frame(&mut self) {
        while self.running {
            let ecl = self.ecl.clone().unwrap();
            let sub = &ecl.subs[self.sub as usize];
            let call = match sub.instructions.get(self.ip as usize) {
                Some(call) => call,
                None => {
                    self.running = false;
                    break;
                }
            };

            if call.time > self.frame {
                break;
            }
            self.ip += 1;

            let rank = self.enemy.borrow().get_rank();
            if (call.rank_mask & rank).is_empty() {
                continue;
            }

            if call.time == self.frame {
                self.run_instruction(call.instr.clone());
            }
        }
        self.frame += 1;
    }

    fn get_i32(&self, var: i32) -> i32 {
        let enemy = self.enemy.borrow();
        match var {
            -10001 => self.variables.0[0],
            -10002 => self.variables.0[1],
            -10003 => self.variables.0[2],
            -10004 => self.variables.0[3],
            -10005 => self.variables.1[0] as i32,
            -10006 => self.variables.1[1] as i32,
            -10007 => self.variables.1[2] as i32,
            -10008 => self.variables.1[3] as i32,
            -10009 => self.variables.2[0],
            -10010 => self.variables.2[1],
            -10011 => self.variables.2[2],
            -10012 => self.variables.2[3],
            -10013 => enemy.get_rank().bits() as i32,
            -10014 => enemy.get_difficulty(),
            -10015 => enemy.pos.x as i32,
            -10016 => enemy.pos.y as i32,
            -10017 => enemy.z as i32,
            -10018 => unimplemented!(),
            -10019 => unimplemented!(),
            -10020 => unreachable!(),
            -10021 => unimplemented!(),
            -10022 => enemy.frame as i32,
            -10023 => unreachable!(),
            -10024 => enemy.life as i32,
            -10025 => unimplemented!(),
            _ => var
        }
    }

    fn get_f32(&self, var: f32) -> f32 {
        let enemy = self.enemy.borrow();
        match var {
            -10001.0 => self.variables.0[0] as f32,
            -10002.0 => self.variables.0[1] as f32,
            -10003.0 => self.variables.0[2] as f32,
            -10004.0 => self.variables.0[3] as f32,
            -10005.0 => self.variables.1[0],
            -10006.0 => self.variables.1[1],
            -10007.0 => self.variables.1[2],
            -10008.0 => self.variables.1[3],
            -10009.0 => self.variables.2[0] as f32,
            -10010.0 => self.variables.2[1] as f32,
            -10011.0 => self.variables.2[2] as f32,
            -10012.0 => self.variables.2[3] as f32,
            -10013.0 => enemy.get_rank().bits() as f32,
            -10014.0 => enemy.get_difficulty() as f32,
            -10015.0 => enemy.pos.x,
            -10016.0 => enemy.pos.y,
            -10017.0 => enemy.z,
            -10018.0 => unimplemented!(),
            -10019.0 => unimplemented!(),
            -10020.0 => unreachable!(),
            -10021.0 => unimplemented!(),
            -10022.0 => enemy.frame as f32,
            -10023.0 => unreachable!(),
            -10024.0 => enemy.life as f32,
            -10025.0 => unimplemented!(),
            _ => var
        }
    }

    fn set_i32(&mut self, var: i32, value: i32) {
        let mut enemy = self.enemy.borrow_mut();
        match var {
            -10001 => self.variables.0[0] = value,
            -10002 => self.variables.0[1] = value,
            -10003 => self.variables.0[2] = value,
            -10004 => self.variables.0[3] = value,
            -10005 => unimplemented!(),
            -10006 => unimplemented!(),
            -10007 => unimplemented!(),
            -10008 => unimplemented!(),
            -10009 => self.variables.2[0] = value,
            -10010 => self.variables.2[1] = value,
            -10011 => self.variables.2[2] = value,
            -10012 => self.variables.2[3] = value,
            -10013 => unreachable!(),
            -10014 => unreachable!(),
            -10015 => unimplemented!(),
            -10016 => unimplemented!(),
            -10017 => unimplemented!(),
            -10018 => unreachable!(),
            -10019 => unreachable!(),
            -10020 => unreachable!(),
            -10021 => unreachable!(),
            -10022 => enemy.frame = value as u32,
            -10023 => unreachable!(),
            -10024 => enemy.life = value as u32,
            -10025 => unreachable!(),
            _ => panic!("Unknown variable {}", var)
        }
    }

    fn set_f32(&mut self, var: f32, value: f32) {
        let mut enemy = self.enemy.borrow_mut();
        match var {
            -10001.0 => unimplemented!(),
            -10002.0 => unimplemented!(),
            -10003.0 => unimplemented!(),
            -10004.0 => unimplemented!(),
            -10005.0 => self.variables.1[0] = value,
            -10006.0 => self.variables.1[1] = value,
            -10007.0 => self.variables.1[2] = value,
            -10008.0 => self.variables.1[3] = value,
            -10009.0 => unimplemented!(),
            -10010.0 => unimplemented!(),
            -10011.0 => unimplemented!(),
            -10012.0 => unimplemented!(),
            -10013.0 => unreachable!(),
            -10014.0 => unreachable!(),
            -10015.0 => enemy.pos.x = value,
            -10016.0 => enemy.pos.y = value,
            -10017.0 => enemy.z = value,
            -10018.0 => unreachable!(),
            -10019.0 => unreachable!(),
            -10020.0 => unreachable!(),
            -10021.0 => unreachable!(),
            -10022.0 => unimplemented!(),
            -10023.0 => unreachable!(),
            -10024.0 => unimplemented!(),
            -10025.0 => unreachable!(),
            _ => panic!("Unknown variable {}", var)
        }
    }

    fn get_prng(&mut self) -> Rc<RefCell<Prng>> {
        let enemy = self.enemy.borrow();
        enemy.prng.upgrade().unwrap()
    }

    fn run_instruction(&mut self, instruction: SubInstruction) {
        println!("Running instruction {:?}", instruction);
        match instruction {
            SubInstruction::Noop() => {
                // really
            }
            // 1
            SubInstruction::Destroy(_unused) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.removed = true;
            }
            // 2
            SubInstruction::RelativeJump(frame, ip) => {
                self.frame = frame;
                // ip = ip + flag in th06
                self.ip = ip;
                // we jump back to the main of the interpreter
            }
            // 3
            // GHIDRA SAYS THERE IS A COMPARISON_REG BUFFER BUT THERE IS NOT!!!
            //
            // MOV        ECX,dword ptr [EBP + 0x8]                     jumptable 00407544 case 31
            // CMP        dword ptr [0x9d4 + ECX],0x0
            // JLE        LAB_00407abb
            // aka ECX = enemy pointer
            // ECX->9d4 (aka enemy_pointer_copy->comparison_reg) == 0
            // only the pointer is copied, not the value, thus we are safe
            SubInstruction::RelativeJumpEx(frame, ip, var_id) => {
                // TODO: counter_value is a field of "enemy" in th06, to check
                let counter_value = self.get_i32(var_id) - 1;
                if counter_value > 0 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 4
            SubInstruction::SetInt(var_id, value) => {
                self.set_i32(var_id, value);
            }
            // 5
            SubInstruction::SetFloat(var_id, value) => {
                self.set_f32(var_id as f32, value);
            }
            // 6
            SubInstruction::SetRandomInt(var_id, maxval) => {
                let random = self.get_prng().borrow_mut().get_u32() as i32;
                self.set_i32(var_id, random % self.get_i32(maxval));
            }
            // 7
            /*
            SubInstruction::SetRandomIntMin(var_id, maxval, minval) => {
                self.set_i32(var_id, (self.get_prng().borrow_mut().get_u32() % self.get_i32(maxval)) + self.get_i32(minval));
            }
            */
            // 8
            SubInstruction::SetRandomFloat(var_id, maxval) => {
                let random = self.get_prng().borrow_mut().get_f64() as f32;
                self.set_f32(var_id as f32, self.get_f32(maxval) * random)
            }
            // 9
            SubInstruction::SetRandomFloatMin(var_id, maxval, minval) => {
                let random = self.get_prng().borrow_mut().get_f64() as f32;
                self.set_f32(var_id as f32, self.get_f32(maxval) * random + self.get_f32(minval))
            }
            // 10
            SubInstruction::StoreX(var_id) => {
                let x = {
                    let enemy = self.enemy.borrow();
                    enemy.pos.x
                };
                // TODO: is this really an i32?
                self.set_i32(var_id, x as i32);
            }
            // 11
            /*
            SubInstruction::StoreY(var_id) => {
                let enemy = self.enemy.borrow();
                self.set_i32(var_id, enemy.pos.y);
            }
            */
            // 12
            /*
            SubInstruction::StoreZ(var_id) => {
                let enemy = self.enemy.borrow();
                self.set_i32(var_id, enemy.z);
            }
            */
            // 13(int), 20(float), same impl in th06
            SubInstruction::AddInt(var_id, a, b) => {
                self.set_i32(var_id, self.get_i32(a) + self.get_i32(b));
            }
            SubInstruction::AddFloat(var_id, a, b) => {
                self.set_f32(var_id as f32, self.get_f32(a) + self.get_f32(b));
            }
            // 14(int), 21(float), same impl in th06
            SubInstruction::SubstractInt(var_id, a, b) => {
                self.set_i32(var_id, self.get_i32(a) - self.get_i32(b));
            }
            SubInstruction::SubstractFloat(var_id, a, b) => {
                self.set_f32(var_id as f32, self.get_f32(a) - self.get_f32(b));
            }
            // 15(int), 22(unused)
            SubInstruction::MultiplyInt(var_id, a, b) => {
                self.set_i32(var_id, self.get_i32(a) * self.get_i32(b));
            }
            /*
            SubInstruction::MultiplyFloat(var_id, a, b) => {
                self.set_f32(var_id as f32, self.get_f32(a) * self.get_f32(b));
            }
            */
             // 16(int), 23(unused)
            SubInstruction::DivideInt(var_id, a, b) => {
                self.set_i32(var_id, self.get_i32(a) / self.get_i32(b));
            }
            /*
            SubInstruction::Divide(var_id, a, b) => {
                self.set_f32(var_id as f32, self.get_f32(a) / self.get_f32(b));
            }
            */
            // 17(int) 24(unused)
            SubInstruction::ModuloInt(var_id, a, b) => {
                self.set_i32(var_id, self.get_i32(a) % self.get_i32(b));
            }
            /*
            SubInstruction::ModuloFloat(var_id, a, b) => {
                self.set_f32(var_id as f32, self.get_f32(a) % self.get_f32(b));
            }
            */
            // 18
            // setval used by pytouhou, but not in game(???)
            SubInstruction::Increment(var_id) => {
                self.set_i32(var_id, self.get_i32(var_id) + 1);
            }
            // 19
            /*
            SubInstruction::Decrement(var_id) => {
                self.set_i32(var_id, self.get_i32(var_id) - 1);
            }
            */
            //25
            SubInstruction::GetDirection(var_id, x1, y1, x2, y2) => {
                //__ctrandisp2 in ghidra, let's assume from pytouhou it's atan2
                self.set_f32(var_id as f32, (self.get_f32(y2) - self.get_f32(y1)).atan2(self.get_f32(x2) - self.get_f32(x1)));
            }

            // 26
            SubInstruction::FloatToUnitCircle(var_id) => {
                // TODO: atan2(var_id, ??) is used by th06, maybe ?? is pi?
                // we suck at trigonometry so let's use pytouhou for now
                self.set_f32(var_id as f32, (self.get_f32(var_id as f32) + std::f32::consts::PI) % (2. * std::f32::consts::PI) - std::f32::consts::PI);
            }

            // 27(int), 28(float)
            SubInstruction::CompareInts(a, b) => {
                let a = self.get_i32(a);
                let b = self.get_i32(b);
                if a < b {
                    self.comparison_reg = -1;
                }
                else if  a == b {
                    self.comparison_reg = 0;
                }
                else {
                    self.comparison_reg = 1;
                }
            }
            SubInstruction::CompareFloats(a, b) => {
                let a = self.get_f32(a);
                let b = self.get_f32(b);
                if a < b {
                    self.comparison_reg = -1;
                }
                else if  a == b {
                    self.comparison_reg = 0;
                }
                else {
                    self.comparison_reg = 1;
                }
            }
            // 29
            SubInstruction::RelativeJumpIfLowerThan(frame, ip) => {
                if self.comparison_reg == -1 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 30
            SubInstruction::RelativeJumpIfLowerOrEqual(frame, ip) => {
                if self.comparison_reg != 1 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 31
            SubInstruction::RelativeJumpIfEqual(frame, ip) => {
                if self.comparison_reg == 0 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 32
            SubInstruction::RelativeJumpIfGreaterThan(frame, ip) => {
                if self.comparison_reg == 1 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 33
            SubInstruction::RelativeJumpIfGreaterOrEqual(frame, ip) => {
                if self.comparison_reg != -1 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 34
            SubInstruction::RelativeJumpIfNotEqual(frame, ip) => {
                if self.comparison_reg != 0 {
                    SubInstruction::RelativeJump(frame, ip);
                }
            }
            // 35
            SubInstruction::Call(sub, param1, param2) => {
                // does insane stuff with the stack, not implemented
                unimplemented!()
            }

            // 36
            SubInstruction::Return() => {
                // does insane stuff with the stack, not implemented
                unimplemented!()
            }
            // 37
            /*
            SubInstruction::CallIfSuperior(sub, param1, param2, a, b) => {
                if self.get_i32(b) <= self.get_i32(a) {
                    SubInstruction::Call(sub, param1, param2);
                }
            }
            */
            // 38
            /*
            SubInstruction::CallIfSuperiorOrEqual(sub, param1, param2, a, b) => {
                if self.get_i32(b) <= self.get_i32(a) {
                    SubInstruction::Call(sub, param1, param2);
                }
            }
            */
            // 39
            SubInstruction::CallIfEqual(sub, param1, param2, a, b) => {
                if self.get_i32(b) == self.get_i32(a) {
                    SubInstruction::Call(sub, param1, param2);
                }
            }
            // 40
            /*
            SubInstruction::CallIfEqual(sub, param1, param2, a, b) => {
                if self.get_i32(b) == self.get_i32(a) {
                    SubInstruction::Call(sub, param1, param2);
                }
            }
            */
            //41
            /*
            SubInstruction::CallIfInferior(sub, param1, param2, a, b) => {
                if self.get_i32(a) < self.get_i32(b) {
                    SubInstruction::Call(sub, param1, param2);
                }
            }
            */
            //42
            /*
            SubInstruction::CallIfInferiorOrEqual(sub, param1, param2, a, b) => {
                if self.get_i32(a) <= self.get_i32(b) {
                    SubInstruction::Call(sub, param1, param2);
                }
            }
            */
            // 43
            SubInstruction::SetPosition(x, y, z) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.set_pos(self.get_f32(x), self.get_f32(y), self.get_f32(z));
            }
            // 44
            /*
            SubInstruction::SetAngularSpeed(x, y, z) => {
                // same as above, except for angular speed
                let mut enemy = self.enemy.borrow_mut();
                enemy.set_angular_speed(self.get_f32(x), self.get_f32(y), self.get_f32(z));
            }
            */
            // 45
            SubInstruction::SetAngleAndSpeed(angle, speed) => {
                let angle = self.get_f32(angle);
                let speed = self.get_f32(speed);
                let mut enemy = self.enemy.borrow_mut();
                enemy.update_mode = 0;
                enemy.angle = angle;
                enemy.speed = speed;
            }
            // 46
            SubInstruction::SetRotationSpeed(speed) => {
                let rotation_speed = self.get_f32(speed);
                let mut enemy = self.enemy.borrow_mut();
                enemy.update_mode = 0;
                enemy.rotation_speed = rotation_speed;
            }
            // 47
            SubInstruction::SetSpeed(speed) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.update_mode = 0;
                enemy.speed = self.get_f32(speed);
            }
            // 48
            SubInstruction::SetAcceleration(acceleration) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.update_mode = 0;
                enemy.acceleration = self.get_f32(acceleration);
            }
            // 49
            SubInstruction::SetRandomAngle(min_angle, max_angle) => {
                let angle = self.get_prng().borrow_mut().get_f64() as f32 * (max_angle - min_angle) + min_angle;
                let mut enemy = self.enemy.borrow_mut();
                enemy.angle = angle;
            }
            // 51
             /*
            SubInstruction::TargetPlayer(angle, speed) => {
                let mut enemy = self.enemy.borrow_mut();
                let player = enemy.select_player();
                enemy.update_mode = 0;
                enemy.speed = speed;
                enemy.angle = enemy.get_angle(player) + angle;

            }
            */
            // 52 to 64 are different interlacing fields

            // 65
            // to note: in game a flag is set to enable the screenbox and is set by 66 to disable
            // it on top of setting our values. But we have a good engine and can detect if that's
            // changed without setting a flag :)
            SubInstruction::SetScreenBox(xmin, ymin, xmax, ymax) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.screen_box = Some((xmin, ymin, xmax, ymax));
            }
             // 66
            SubInstruction::ClearScreenBox() => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.screen_box = None;
            }
            // 67 to 75 are set bullet attributes and it seems a pain to reverse rn



            // 78-79 are more interpolation flags 
            // 78
            SubInstruction::DelayAttack() => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.delay_attack = true;
            }
            // 79
            SubInstruction::NoDelayAttack() => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.delay_attack = false;
            }
            // 80
            /*
            SubInstruction::NoClue() => {
                let mut enemy = self.enemy.borrow_mut();
                //bullet_pos = launch offset
                (enemy->bullet_attributes).bullets_per_shot = enemy.pos.x + enemy->bullet_pos.pos.x;
                (enemy->bullet_attributes).number_of_shots = enemy.pos.pos.y + enemy.bullet_pos.pos.y;
                (enemy->bullet_attributes).speed = enemy.z + bullet_pos.z;
                enemy.fire(bullet_attributes=bullet_attributes)
            }
            */
            // 81
            /*
            SubInstruction::SetBulletLaunchOffset(x, y, z) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.bullet_launch_offset = (self._getval(x), self._getval(y), self._getval(z));
            }
            */
            // 82
            // TODO: correct but how to implement that in a rusty way?
            /*
            SubInstruction::SetExtendedBulletAttributes(x, y, z) => {
                let mut enemy = self.enemy.borrow_mut();

                // self._enemy.extended_bullet_attributes = tuple(self._getval(attr) for attr in attributes)
            }
            */
            // 83
            /*
            SubInstruction::ChangeBulletsIntoStarBonus() => {
                let mut game = self.game.borrow_mut();
                game.change_bullets_into_star_items();
            }
            */
            // 84
            // WARNING: dead code. If the parameter is < 0 it unsets a bullet_flag, otherwise it
            // sets it, never using the parameter ever
            /*
            SubInstruction::UNK_ins84() => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.bullet_flag_something
            }
            */

            // 85-86 ire newlaser functions

            // 87
            SubInstruction::SetUpcomingLaserId(laser_id) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.current_laser_id = laser_id;
            }

            // 88
            
            SubInstruction::AlterLaserAngle(laser_id, delta) => {
                let mut enemy = self.enemy.borrow_mut();
                if enemy.laser_by_id.contains_key(&laser_id) {
                    let mut laser = enemy.laser_by_id.get(laser_id);
                    laser.angle += self.get_f32(delta);
                }
            }
            
            // 89
            /*
            SubInstruction::AlterLaserAnglePlayer(laser_id, delta) => {
                let mut enemy = self.enemy.borrow_mut();
                if enemy.laser_by_id.contains_key(&laser_id) {
                    let mut laser = enemy.laser_by_id.get(laser_id);
                    let player = enemy.select_player();
                    laser.angle = enemy.get_angle(player) + angle;
                }
            }
            */

            // 90
            SubInstruction::RepositionLaser(laser_id, ox, oy, oz) => {
                let mut enemy = self.enemy.borrow_mut();
                if enemy.laser_by_id.contains_key(&laser_id) {
                    let mut laser = enemy.laser_by_id.get(laser_id);
                    laser.set_base_pos(enemy.pos.x + ox, enemy.pos.y + oy, enemy.z + oz)
                }
            }
            // 91
            // wat
            SubInstruction::LaserSetCompare(laser_id) => {
                let mut enemy = self.enemy.borrow_mut();
                // in game it checks if either the laser exists OR if one of its member is set to 0
                // which, uhhhh, we are not going to reimplement for obvious reasons
                // the correct implementation would be: if this laser does not exist have a
                // 1/100000 chance to continue, otherwise crash
                if enemy.laser_by_id.contains_key(&laser_id) {
                    // let's assume we gud 
                    self.comparison_reg = 1;
                } 
                else{
                    self.comparison_reg = 0;
                }
            }

            // 92
            /*
            SubInstruction::RepositionLaser(laser_id, ox, oy, oz) => {
                let mut enemy = self.enemy.borrow_mut();
                if enemy.laser_by_id.contains_key(&laser_id) {
                    let mut laser = enemy.laser_by_id.get(laser_id);
                    laser.cancel();
                }
            }
            */






            // 97
            SubInstruction::SetAnim(index) => {
                // seems correct, game internally gets base_addr =(iVar13 + 0x1c934), pointer_addr = iVar14 * 4
                let mut enemy = self.enemy.borrow_mut();
                enemy.set_anim(index as u8);
            }
            // 98
            SubInstruction::SetMultipleAnims(default, end_left, end_right, left, right, _unused) => {
                // _unused was supposed to set movement_dependant_sprites, but internally the game
                // assigns it 0xff
                // TODO: THIS DOES NOT CALL set_anim. this only assigns all parameters to their
                // internal struct. To check if the anims are set somewhere else
                let mut enemy = self.enemy.borrow_mut();
                enemy.movement_dependant_sprites = if left == -1 {
                    None
                } else {
                    enemy.set_anim(default as u8);
                    Some((end_left as u8, end_right as u8, left as u8, right as u8))
                };
            }

            // 100
            SubInstruction::SetDeathAnim(index) => {
                // TODO: takes 3 parameters in game as u8 unlike our single u32.
                // To reverse!
                let mut enemy = self.enemy.borrow_mut();
                enemy.death_anim = index;
            }

            // 103
            SubInstruction::SetHitbox(width, height, depth) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.set_hitbox(width, height);
            }

            // 104
            SubInstruction::SetCollidable(collidable) => {
                // TODO: me and my siblings(105, 107, 117) are implemented as a single variable in the touhou 6
                // original engine. While our behaviour seems correct we might want to implement
                // that as a single variable
                // TODO[2]: THE BITFLAG MIGHT BE INCORRECT FOR OTHER SIBLING INSTRUCTIONS, the
                // behavior was DEFINITELY incorrect in pytouhou for SetTouchable at the very least
                let mut enemy = self.enemy.borrow_mut();
                enemy.collidable = (collidable&1) != 0;
            }

            // 105
            SubInstruction::SetDamageable(damageable) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.damageable = (damageable&1) != 0;
            }

            // 106
            /*
            SubInstruction::PlaySound(index) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.play_sound(index);
            }
            */

            // 107
            SubInstruction::SetDeathFlags(death_flags) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.death_flags = death_flags;
            }

            // 109
            SubInstruction::MemoryWriteInt(value, index) => {
                unimplemented!("not again that damn foe corrupted my ret\\x41\\x41\\x41\\x41");
            }


            // 117
            SubInstruction::SetTouchable(touchable) => {
                let mut enemy = self.enemy.borrow_mut();
                enemy.touchable = touchable != 0;
            }

            // 121
            // Here lies the Di Sword of sadness
            SubInstruction::CallSpecialFunction(function, arg) => {
                unimplemented!("spellcards are a bitch and a half");
            }

            _ => unimplemented!("{:?}", instruction)
        }
    }
}
