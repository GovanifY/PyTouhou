//! ECL runner.

use crate::th06::anm0::{
    Script,
    Anm0,
    Call,
    Instruction,
};
use crate::th06::interpolator::{Interpolator1, Interpolator2, Interpolator3, Formula};
use crate::util::math::Mat4;
use crate::util::prng::Prng;
use std::cell::RefCell;
use std::rc::{Rc, Weak};

    fn run_instruction(&mut self, instruction: Instruction) {
        let mut sprite = self.sprite.borrow_mut();
        match instruction {
            Instruction::Noop() {
                // really
            }
            // 1
            Instruction::Stop() {
                self._enemy.removed = true;
            }
            // 2 
            Instruction::RelativeJump(frame, ip) {
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
            Instruction::RelativeJumpEx(frame, ip, var_id) {
                // TODO: counter_value is a field of "enemy" in th06, to check
                counter_value = self._getval(var_id) - 1
                    if counter_value > 0 {
                        Instruction::RelativeJump(frame, ip);
                    }
            }

            //4, 5
            Instruction::SetVariable(var_id, value) {
                self._setval(var_id, value);
            }
            // 6
            Instruction::SetRandomInt(var_id, maxval) {
                self._setval(var_id, self._game.prng.rand_32()%self._getval(maxval));
            }
            // 7
            Instruction::SetRandomIntMin(var_id, maxval, minval) {
                self._setval(var_id, (self._game.prng.rand_32()%self._getval(maxval))+self._getval(minval));
            }
            // 8
            Instruction::SetRandomFloat(var_id, maxval) {
                self._setval(var_id, self._getval(maxval) * self._game.prng.rand_double())
            }
            // 9
            Instruction::SetRandomFloatMin(var_id, maxval, minval) {
                self._setval(var_id, (self._getval(maxval) * self._game.prng.rand_double())+self._getval(minval))
            }
            // 10
            Instruction::StoreX(var_id) {
                self._setval(var_id, self._enemy.x);
            }
            // 11
            Instruction::StoreY(var_id) {
                self._setval(var_id, self._enemy.y);
            }
            // 12
            Instruction::StoreZ(var_id) {
                self._setval(var_id, self._enemy.z);
            }
            // 13(int), 20(float), same impl in th06
            Instruction::Add(var_id, a, b) {
                self._setval(var_id, self._getval(a) + self._getval(b));
            }
            // 14(int), 21(float), same impl in th06
            Instruction::Substract(var_id, a, b) {
                self._setval(var_id, self._getval(a) - self._getval(b));
            }
            // 15(int), 22(unused)
            Instruction::Multiply(var_id, a, b) {
                self._setval(var_id, self._getval(a) * self._getval(b));
            }
             // 16(int), 23(unused)
            Instruction::Divide(var_id, a, b) {
                self._setval(var_id, self._getval(a) / self._getval(b));
            }
            // 17(int) 24(unused)
            Instruction::Divide(var_id, a, b) {
                self._setval(var_id, self._getval(a) % self._getval(b));
            }
            // 18
            // setval used by pytouhou, but not in game(???)
            Instruction::Increment(var_id) {
                var_id = self._getval(var_id) + 1
            }
            // 19
            Instruction::Decrement(var_id) {
                var_id = self._getval(var_id) - 1
            }
            //25
            Instruction::GetDirection(var_id, x1, y1, x2, y2) {
                //__ctrandisp2 in ghidra, let's assume from pytouhou it's atan2
                self._setval(var_id, atan2(self._getval(y2) - self._getval(y1), self._getval(x2) - self._getval(x1)));
            }

            // 26
            Instruction::FloatToUnitCircle(var_id) {
                // TODO: atan2(var_id, ??) is used by th06, maybe ?? is pi? 
                // we suck at trigonometry so let's use pytouhou for now
                self._setval(var_id, (self._getval(var_id) + pi) % (2*pi) - pi);
            }

            // 27(int), 28(float)
            Instruction::Compare(a, b) {
                a = self._getval(a);
                b = self._getval(b);
                if a < b {
                    self.comparison_reg = -1 
                }
                else if  a == b {
                    self.comparison_reg = 0 
                }
                else {
                    self.comparison_reg = 1 
                }
            }
            // 29 
            Instruction::RelativeJumpIfLowerThan(frame, ip) {
                if self.comparison_reg == -1 {
                    Instruction::RelativeJump(); 
                }
            }
            // 30 
            Instruction::RelativeJumpIfLowerOrEqual(frame, ip) {
                if self.comparison_reg != 1 {
                    Instruction::RelativeJump(); 
                }
            }
            // 31 
            Instruction::RelativeJumpIfEqual(frame, ip) {
                if self.comparison_reg == 0 {
                    Instruction::RelativeJump(); 
                }
            }
            // 32 
            Instruction::RelativeJumpIfGreaterThan(frame, ip) {
                if self.comparison_reg == 1 {
                    Instruction::RelativeJump(); 
                }
            }
            // 33
            Instruction::RelativeJumpIfGreaterOrEqual(frame, ip) {
                if self.comparison_reg != -1
                    Instruction::RelativeJump();
            }
            // 34
            Instruction::RelativeJumpIfNotEqual(frame, ip) {
                if self.comparison_reg != 0
                    Instruction::RelativeJump();
            }
            // 35
            Instruction::Call(sub, param1, param2) {
                // does insane stuff with the stack, not implemented 
            }
 
            // 36
            Instruction::Ret(frame, ip) {
                // does insane stuff with the stack, not implemented 
            }
            // 37
            Instruction::CallIfSuperior(sub, param1, param2, a, b) {
                if(self._getval(b) <= self._getval(a)) {
                    Instruction::Call(sub, param1, param2);
                }
            }
            // 38
            Instruction::CallIfSuperiorOrEqual(sub, param1, param2, a, b) {
                if(self._getval(b) <= self._getval(a)) {
                    Instruction::Call(sub, param1, param2);
                }
            }
            // 39
            Instruction::CallIfEqual(sub, param1, param2, a, b) {
                if(self._getval(b) == self._getval(a)) {
                    Instruction::Call(sub, param1, param2);
                }
            }
            // 40 
            Instruction::CallIfEqual(sub, param1, param2, a, b) {
                if(self._getval(b) == self._getval(a)) {
                    Instruction::Call(sub, param1, param2);
                }
            }
            //41 
            Instruction::CallIfInferior(sub, param1, param2, a, b) {
                if(self._getval(a) < self._getval(b)) {
                    Instruction::Call(sub, param1, param2);
                }
            }
            //42 
            Instruction::CallIfInferiorOrEqual(sub, param1, param2, a, b) {
                if(self._getval(a) <= self._getval(b)) {
                    Instruction::Call(sub, param1, param2);
                }
            }
            // 43 
            Instruction::SetPos(x, y, z) {
                self._enemy.set_pos(self._getval(x), self._getval(y), self._getval(z));
            }
            // 44 
            Instruction::SetPosInterlacing(x, y, z) {
                //TODO: almost the same as setpos, except with 3 different values and sets the
                //interlacing, should double check 
                self._enemy.set_pos(self._getval(x), self._getval(y), self._getval(z));
            }
            // 45
            Instruction::SetAngleSpeed(angle, speed) {
                self._enemy.update_mode = 0;
                self._enemy.angle, self._enemy.speed = self._getval(angle), self._getval(speed);
            }
            // 46 
            Instruction::SetRotationSpeed(speed) {
                self._enemy.update_mode = 0
                self._enemy.rotation_speed = self._getval(speed)
            }
            // 47 
            Instruction::SetSpeed(speed) {
                self._enemy.update_mode = 0
                self._enemy.speed = self._getval(speed)
            }
            // 48 
            Instruction::SetAcceleration(acceleration) {
                self._enemy.update_mode = 0
                self._enemy.acceleration = self._getval(acceleration)
            }
            // 49
            Instruction::SetRandomAngle(min_angle, max_angle) {
                angle = self._game.prng.rand_double() * (max_angle - min_angle) + min_angle
                self._enemy.angle = angle
            }

            // 83 -> star items >>> life items










