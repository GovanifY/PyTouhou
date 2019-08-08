//! ECL enemy script format support.

use nom::{
    IResult,
    bytes::complete::take_while_m_n,
    number::complete::{le_u8, le_u16, le_u32, le_i16, le_i32, le_f32},
};
use encoding_rs::SHIFT_JIS;

/// A single instruction, part of a `Script`.
#[derive(Debug, Clone)]
pub struct CallSub {
    /// Time at which this instruction will be called.
    pub time: u32,

    /// TODO
    pub rank_mask: u16,

    /// TODO
    pub param_mask: u16,

    /// The instruction to call.
    pub instr: SubInstruction,
}

/// Script driving an animation.
#[derive(Debug, Clone)]
pub struct Sub {
    /// List of instructions in this script.
    pub instructions: Vec<CallSub>,
}

/// A single instruction, part of a `Script`.
#[derive(Debug, Clone)]
pub struct CallMain {
    /// Time at which this instruction will be called.
    pub time: u16,

    /// Subroutine to call for this enemy.
    pub sub: u16,

    /// The instruction to call.
    pub instr: MainInstruction,
}

/// Script driving an animation.
#[derive(Debug, Clone)]
pub struct Main {
    /// List of instructions in this script.
    pub instructions: Vec<CallMain>,
}

/// Main struct of the ANM0 animation format.
#[derive(Debug, Clone)]
pub struct Ecl {
    /// A list of subs.
    pub subs: Vec<Sub>,

    /// A list of mains.
    pub mains: Vec<Main>,
}

impl Ecl {
    /// Parse a slice of bytes into an `Ecl` struct.
    pub fn from_slice(data: &[u8]) -> IResult<&[u8], Ecl> {
        parse_ecl(data)
    }
}

macro_rules! declare_main_instructions {
    ($($opcode:tt => fn $name:ident($($arg:ident: $arg_type:ident),*)),*,) => {
        /// Available instructions in an `Ecl`.
        #[allow(missing_docs)]
        #[derive(Debug, Clone, Copy)]
        pub enum MainInstruction {
            $(
                $name($($arg_type),*)
            ),*
        }

        fn parse_main_instruction_args(input: &[u8], opcode: u16) -> IResult<&[u8], MainInstruction> {
            let mut i = &input[..];
            let instr = match opcode {
                $(
                    $opcode => {
                        $(
                            let (i2, $arg) = concat_idents!(le_, $arg_type)(i)?;
                            i = i2;
                        )*
                        MainInstruction::$name($($arg),*)
                    }
                )*
                _ => unreachable!()
            };
            Ok((i, instr))
        }
    };
}

/// XXX
pub fn le_String(i: &[u8]) -> IResult<&[u8], String> {
    let (string, encoding, replaced) = SHIFT_JIS.decode(i);
    Ok((&i[34..], string.into_owned()))
}

macro_rules! declare_sub_instructions {
    ($($opcode:tt => fn $name:ident($($arg:ident: $arg_type:ident),*)),*,) => {
        /// Available instructions in an `Ecl`.
        #[allow(missing_docs)]
        #[derive(Debug, Clone)]
        pub enum SubInstruction {
            $(
                $name($($arg_type),*)
            ),*
        }

        fn parse_sub_instruction_args(input: &[u8], opcode: u16) -> IResult<&[u8], SubInstruction> {
            let mut i = &input[..];
            let instr = match opcode {
                $(
                    $opcode => {
                        $(
                            let (i2, $arg) = concat_idents!(le_, $arg_type)(i)?;
                            i = i2;
                        )*
                        SubInstruction::$name($($arg),*)
                    }
                )*
                _ => unreachable!()
            };
            Ok((i, instr))
        }
    };
}

declare_main_instructions!{
    0 => fn SpawnEnemy(x: f32, y: f32, z: f32, life: i16, bonus_dropped: i16, die_score: u32),
    2 => fn SpawnEnemyMirrored(x: f32, y: f32, z: f32, life: i16, bonus_dropped: i16, die_score: u32),
    4 => fn SpawnEnemyRandom(x: f32, y: f32, z: f32, life: i16, bonus_dropped: i16, die_score: u32),
    6 => fn SpawnEnemyMirroredRandom(x: f32, y: f32, z: f32, life: i16, bonus_dropped: i16, die_score: u32),
    8 => fn CallMessage(),
    9 => fn WaitMessage(),
    10 => fn ResumeEcl(x: f32, y: f32),
    12 => fn WaitForBossDeath(),
}

declare_sub_instructions!{
    0 => fn Noop(),
    1 => fn Destroy(unused: u32),
    2 => fn RelativeJump(frame: u32, ip: i32),
    3 => fn RelativeJumpEx(frame: u32, ip: i32, variable_id: i32),
    4 => fn SetInt(var: i32, value: i32),
    5 => fn SetFloat(var: i32, value: f32),
    6 => fn SetRandomInt(var: i32, max: i32),
    8 => fn SetRandomFloat(var: i32, max: f32),
    9 => fn SetRandomFloat2(var: i32, amplitude: f32, min: f32),
    10 => fn StoreX(var: i32),
    13 => fn AddInt(var: i32, a: i32, b: i32),
    14 => fn SubstractInt(var: i32, a: i32, b: i32),
    15 => fn MultiplyInt(var: i32, a: i32, b: i32),
    16 => fn DivideInt(var: i32, a: i32, b: i32),
    17 => fn Modulo(var: i32, a: i32, b: i32),
    18 => fn Increment(var: i32),
    20 => fn AddFloat(var: i32, a: f32, b: f32),
    21 => fn SubstractFloat(var: i32, a: f32, b: f32),
    23 => fn DivideFloat(var: i32, a: f32, b: f32),
    25 => fn GetDirection(var: i32, x1: f32, y1: f32, x2: f32, y2: f32),
    26 => fn FloatToUnitCircle(var: i32),
    27 => fn CompareInts(a: i32, b: i32),
    28 => fn CompareFloats(a: f32, b: f32),
    29 => fn RelativeJumpIfLowerThan(frame: i32, ip: i32),
    30 => fn RelativeJumpIfLowerOrEqual(frame: i32, ip: i32),
    31 => fn RelativeJumpIfEqual(frame: i32, ip: i32),
    32 => fn RelativeJumpIfGreaterThan(frame: i32, ip: i32),
    33 => fn RelativeJumpIfGreaterOrEqual(frame: i32, ip: i32),
    34 => fn RelativeJumpIfNotEqual(frame: i32, ip: i32),
    35 => fn Call(sub: i32, param1: i32, param2: f32),
    36 => fn Return(),
    39 => fn CallIfEqual(sub: i32, param1: i32, param2: f32, a: i32, b: i32),
    43 => fn SetPosition(x: f32, y: f32, z: f32),
    45 => fn SetAngleAndSpeed(angle: f32, speed: f32),
    46 => fn SetRotationSpeed(speed: f32),
    47 => fn SetSpeed(speed: f32),
    48 => fn SetAcceleration(acceleration: f32),
    49 => fn SetRandomAngle(min: f32, max: f32),
    50 => fn SetRandomAngleEx(min: f32, max: f32),
    51 => fn TargetPlayer(TODO: f32, speed: f32),
    52 => fn MoveInDecel(duration: i32, angle: f32, speed: f32),
    56 => fn MoveToLinear(duration: i32, x: f32, y: f32, z: f32),
    57 => fn MoveToDecel(duration: i32, x: f32, y: f32, z: f32),
    59 => fn MoveToAccel(duration: i32, x: f32, y: f32, z: f32),
    61 => fn StopIn(duration: i32),
    63 => fn StopInAccel(duration: i32),
    65 => fn SetScreenBox(xmin: f32, ymin: f32, xmax: f32, ymax: f32),
    66 => fn ClearScreenBox(),
    67 => fn SetBulletAttributes1(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    68 => fn SetBulletAttributes2(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    69 => fn SetBulletAttributes3(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    70 => fn SetBulletAttributes4(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    71 => fn SetBulletAttributes5(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    74 => fn SetBulletAttributes6(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    75 => fn SetBulletAttributes7(anim: i16, sprite_index_offset: i16, bullets_per_shot: i32, number_of_shots: i32, speed: f32, speed2: f32, launch_angle: f32, angle: f32, flags: i32),
    76 => fn SetBulletInterval(interval: i32),
    77 => fn SetBulletIntervalEx(interval: i32),
    78 => fn DelayAttack(),
    79 => fn NoDelayAttack(),
    81 => fn SetBulletLaunchOffset(x: f32, y: f32, z: f32),
    82 => fn SetExtendedBulletAttributes(a: i32, b: i32, c: i32, d: i32, e: f32, f: f32, g: f32, h: f32),
    83 => fn ChangeBulletsInStarBonus(),
    // 84: ('i', None),
    85 => fn NewLaser(laser_type: i16, sprite_idx_offset: i16, angle: f32, speed: f32, start_offset: f32, end_offset: f32, max_length: f32, width: f32, start_duration: i32, duration: i32, end_duration: i32, grazing_delay: i32, grazing_extra_duration: i32, UNK1: i32),
    86 => fn NewLaserTowardsPlayer(laser_type: i16, sprite_idx_offset: i16, angle: f32, speed: f32, start_offset: f32, end_offset: f32, max_length: f32, width: f32, start_duration: i32, duration: i32, end_duration: i32, grazing_delay: i32, grazing_extra_duration: i32, UNK1: i32),
    87 => fn SetUpcomingLaserId(id: i32),
    88 => fn AlterLaserAngle(id: i32, delta: f32),
    90 => fn RepositionLaser(id: i32, ox: f32, oy: f32, oz: f32),
    92 => fn CanceLaser(id: i32),
    93 => fn SetSpellcard(face: i16, number: i16, name: String),
    94 => fn Endspellcard(),
    95 => fn SpawnEnemy(sub: i32, x: f32, y: f32, z: f32, life: i16, bonus_dropped: i16, die_score: i32),
    96 => fn KillAllEnemies(),
    97 => fn SetAnim(script: i32),
    98 => fn SetMultipleAnims(default: i16, end_left: i16, end_right: i16, left: i16, right: i16, UNUSED: i16),
    99 => fn SetAuxAnm(number: i32, script: i32),
    100 => fn SetDeathAnim(sprite_index: i32),
    101 => fn SetBossMode(value: i32),
    102 => fn CreateSquares(UNK1: i32, UNK2: f32, UNK3: f32, UNK4: f32, UNK5: f32),
    103 => fn SetEnemyHitbox(width: f32, height: f32, depth: f32),
    104 => fn SetCollidable(collidable: i32),
    105 => fn SetDamageable(damageable: i32),
    106 => fn PlaySound(index: i32),
    107 => fn SetDeathFlags(death_flags: i32),
    108 => fn SetDeathCallback(sub: i32),
    109 => fn MemoryWriteInt(value: i32, index: i32),
    111 => fn SetLife(life: i32),
    112 => fn SetEllapsedTime(frame: i32),
    113 => fn SetLowLifeTrigger(trigger: i32),
    114 => fn SetLowLifeCallback(sub: i32),
    115 => fn SetTimeout(timeout: i32),
    116 => fn SetTimeoutCallback(sub: i32),
    117 => fn SetTouchable(touchable: i32),
    118 => fn DropParticles(anim: i32, number: u32, r: u8, g: u8, b: u8, UNUSED: u8),
    119 => fn DropBonus(number: i32),
    120 => fn SetAutomaticOrientation(automatic: i32),
    121 => fn CallSpecialFunction(function: i32, argument: i32),
    122 => fn UNK1(TODO: i32),
    123 => fn SkipFrames(frames: i32),
    124 => fn DropSpecificBonus(type_: i32),
    125 => fn UNK2(),
    126 => fn SetRemainingLives(lives: i32),
    127 => fn UNK3(TODO: i32),
    128 => fn Interrupt(event: i32),
    129 => fn InterruptAux(number: i32, event: i32),
    130 => fn UNK5(TODO: i32),
    131 => fn SetDifficultyCoeffs(speed_a: f32, speed_b: f32, nb_a: i32, nb_b: i32, shots_a: i32, shots_b: i32),
    132 => fn SetInvisible(invisible: i32),
    133 => fn CopyCallbacks(),
    134 => fn UNK6(),
    135 => fn EnableSpellcardBonus(UNKNOW: i32),
}

fn parse_ecl(input: &[u8]) -> IResult<&[u8], Ecl> {
    let i = input;

    let (i, sub_count) = le_u16(i)?;
    let (mut i, main_count) = le_u16(i)?;
    assert_eq!(main_count, 0);

    let mut main_offsets = Vec::new();
    for _ in 0..3 {
        let (i2, offset) = le_u32(i)?;
        main_offsets.push(offset as usize);
        i = i2;
    }

    let mut sub_offsets = Vec::new();
    for _ in 0..sub_count {
        let (i2, offset) = le_u32(i)?;
        sub_offsets.push(offset as usize);
        i = i2;
    }

    // Read all subs.
    let mut subs = Vec::new();
    for offset in sub_offsets {
        let mut i = &input[offset..];
        let mut instructions = Vec::new();
        loop {
            let (i2, time) = le_u32(i)?;
            let (i2, opcode) = le_u16(i2)?;
            if time == 0xffffffff || opcode == 0xffff {
                break;
            }

            let (i2, size) = le_u16(i2)?;
            let (i2, rank_mask) = le_u16(i2)?;
            let (i2, param_mask) = le_u16(i2)?;
            // FIXME: this - 12 can trigger a panic, fuzz it!
            let data = &i2[..size as usize - 12];
            let (data, instr) = parse_sub_instruction_args(data, opcode)?;
            assert_eq!(data.len(), 0);
            instructions.push(CallSub { time, rank_mask, param_mask, instr });
            i = &i[size as usize..];
        }
        println!("{:#?}", instructions);
        subs.push(Sub { instructions });
    }

    // Read all mains (always a single one atm).
    let mut mains = Vec::new();
    for offset in main_offsets {
        if offset == 0 {
            break;
        }

        let mut i = &input[offset..];
        let mut instructions = Vec::new();
        loop {
            let (i2, time) = le_u16(i)?;
            let (i2, sub) = le_u16(i2)?;
            if time == 0xffff && sub == 4 {
                break;
            }

            let (i2, opcode) = le_u16(i2)?;
            let (i2, size) = le_u16(i2)?;
            // FIXME: this - 8 can trigger a panic, fuzz it!
            let data = &i2[..size as usize - 8];
            let (data, instr) = parse_main_instruction_args(data, opcode)?;
            assert_eq!(data.len(), 0);
            instructions.push(CallMain { time, sub, instr });
            i = &i[size as usize..];
        }
        mains.push(Main { instructions });
    }

    let ecl = Ecl {
        subs,
        mains,
    };
    Ok((b"", ecl))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{self, Read};
    use std::fs::File;

    #[test]
    fn ecl() {
        let file = File::open("EoSD/ST/ecldata1.ecl").unwrap();
        let mut file = io::BufReader::new(file);
        let mut buf = vec![];
        file.read_to_end(&mut buf).unwrap();
        let (_, ecl) = Ecl::from_slice(&buf).unwrap();
        assert_eq!(ecl.subs.len(), 24);
        assert_eq!(ecl.mains.len(), 1);
    }
}
