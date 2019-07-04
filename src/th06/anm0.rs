//! ANM0 animation format support.

use nom::{
    IResult,
    bytes::complete::{tag, take_while_m_n},
    number::complete::{le_u8, le_u16, le_u32, le_i32, le_f32},
};
use std::collections::HashMap;

/// Coordinates of a sprite into the image.
#[derive(Debug, Clone)]
pub struct Sprite {
    /// Index inside the anm0.
    pub index: u32,

    /// X coordinate in the sprite sheet.
    pub x: f32,

    /// Y coordinate in the sprite sheet.
    pub y: f32,

    /// Width of the sprite.
    pub width: f32,

    /// Height of the sprite.
    pub height: f32,
}

/// A single instruction, part of a `Script`.
#[derive(Debug, Clone)]
pub struct Call {
    /// Time at which this instruction will be called.
    pub time: u16,

    /// The instruction to call.
    pub instr: Instruction,
}

/// Script driving an animation.
#[derive(Debug, Clone)]
pub struct Script {
    /// List of instructions in this script.
    pub instructions: Vec<Call>,

    /// List of interrupts in this script.
    pub interrupts: HashMap<i32, u8>
}

/// Main struct of the ANM0 animation format.
#[derive(Debug, Clone)]
pub struct Anm0 {
    /// Resolution of the image used by this ANM.
    pub size: (u32, u32),

    /// Format of this ANM.
    pub format: u32,

    /// File name of the main image.
    pub first_name: String,

    /// File name of an alpha channel image.
    pub second_name: String,

    /// A list of sprites, coordinates into the attached image.
    pub sprites: Vec<Sprite>,

    /// A map of scripts.
    pub scripts: HashMap<u8, Script>,
}

impl Anm0 {
    /// Parse a slice of bytes into an `Anm0` struct.
    pub fn from_slice(data: &[u8]) -> Result<Anm0, ()> {
        // XXX: report the exact nom error instead!
        let (_, anm0) = parse_anm0(data).or_else(|_| Err(()))?;
        assert_eq!(anm0.len(), 1);
        Ok(anm0[0].clone())
    }
}

fn parse_name(i: &[u8], is_present: bool) -> IResult<&[u8], String> {
    if !is_present {
        return Ok((i, String::new()));
    }
    let (_, slice) = take_while_m_n(0, 32, |c| c != 0)(i)?;
    // XXX: no unwrap!
    let string = String::from_utf8(slice.to_vec()).unwrap();
    Ok((i, string))
}

fn parse_sprite(i: &[u8]) -> IResult<&[u8], Sprite> {
    let (i, index) = le_u32(i)?;
    let (i, x) = le_f32(i)?;
    let (i, y) = le_f32(i)?;
    let (i, width) = le_f32(i)?;
    let (i, height) = le_f32(i)?;
    Ok((i, Sprite {
        index,
        x,
        y,
        width,
        height,
    }))
}

macro_rules! declare_anm_instructions {
    ($($opcode:tt => fn $name:ident($($arg:ident: $arg_type:ident),*)),*,) => {
        /// Available instructions in an `Anm0`.
        #[allow(missing_docs)]
        #[derive(Debug, Clone, Copy)]
        pub enum Instruction {
            $(
                $name($($arg_type),*)
            ),*
        }

        fn parse_instruction_args(input: &[u8], opcode: u8) -> IResult<&[u8], Instruction> {
            let mut i = &input[..];
            let instr = match opcode {
                $(
                    $opcode => {
                        $(
                            let (i2, $arg) = concat_idents!(le_, $arg_type)(i)?;
                            i = i2;
                        )*
                        Instruction::$name($($arg),*)
                    }
                )*
                _ => unreachable!()
            };
            Ok((i, instr))
        }
    };
}

declare_anm_instructions!{
    0 => fn Delete(),
    1 => fn LoadSprite(sprite_number: u32),
    2 => fn SetScale(sx: f32, sy: f32),
    3 => fn SetAlpha(alpha: u32),
    4 => fn SetColor(red: u8, green: u8, blue: u8/*, XXX: x8*/),
    5 => fn Jump(instruction: u32),
    7 => fn ToggleMirrored(),
    9 => fn SetRotations3d(x: f32, y: f32, z: f32),
    10 => fn SetRotationsSpeed3d(x: f32, y: f32, z: f32),
    11 => fn SetScaleSpeed(sx: f32, sy: f32),
    12 => fn Fade(alpha: u32, duration: u32),
    13 => fn SetBlendmodeAdd(),
    14 => fn SetBlendmodeAlphablend(),
    15 => fn KeepStill(),
    16 => fn LoadRandomSprite(min_index: u32, amplitude: u32),
    17 => fn Move(x: f32, y: f32, z: f32),
    18 => fn MoveToLinear(x: f32, y: f32, z: f32, duration: u32),
    19 => fn MoveToDecel(x: f32, y: f32, z: f32, duration: u32),
    20 => fn MoveToAccel(x: f32, y: f32, z: f32, duration: u32),
    21 => fn Wait(),
    22 => fn InterruptLabel(label: i32),
    23 => fn SetCornerRelativePlacement(),
    24 => fn WaitEx(),
    25 => fn SetAllowOffset(allow: u32), // TODO: better name
    26 => fn SetAutomaticOrientation(automatic: u32),
    27 => fn ShiftTextureX(dx: f32),
    28 => fn ShiftTextureY(dy: f32),
    29 => fn SetVisible(visible: u32),
    30 => fn ScaleIn(sx: f32, sy: f32, duration: u32),
    31 => fn Todo(todo: u32),
}

fn parse_anm0(input: &[u8]) -> IResult<&[u8], Vec<Anm0>> {
    let mut list = vec![];
    let start_offset = 0;
    loop {
        let i = &input[start_offset..];
        let (i, num_sprites) = le_u32(i)?;
        let (i, num_scripts) = le_u32(i)?;
        let (i, _) = tag(b"\0\0\0\0")(i)?;
        let (i, width) = le_u32(i)?;
        let (i, height) = le_u32(i)?;
        let (i, format) = le_u32(i)?;
        let (i, _unknown1) = le_u32(i)?;
        let (i, first_name_offset) = le_u32(i)?;
        let (i, _unused) = le_u32(i)?;
        let (i, second_name_offset) = le_u32(i)?;
        let (i, version) = le_u32(i)?;
        let (i, _unknown2) = le_u32(i)?;
        let (i, _texture_offset) = le_u32(i)?;
        let (i, has_data) = le_u32(i)?;
        let (i, _next_offset) = le_u32(i)?;
        let (mut i, unknown3) = le_u32(i)?;

        assert_eq!(version, 0);
        assert_eq!(unknown3, 0);
        assert_eq!(has_data, 0);

        let mut sprite_offsets = vec![];
        for _ in 0..num_sprites {
            let (i2, offset) = le_u32(i)?;
            sprite_offsets.push(offset as usize);
            i = i2;
        }

        let mut script_offsets = vec![];
        for _ in 0..num_scripts {
            let (i2, index) = le_u32(i)?;
            let (i2, offset) = le_u32(i2)?;
            script_offsets.push((index as u8, offset as usize));
            i = i2;
        }

        let i = &input[start_offset + first_name_offset as usize..];
        let (_, first_name) = parse_name(i, first_name_offset > 0)?;

        let i = &input[start_offset + second_name_offset as usize..];
        let (_, second_name) = parse_name(i, second_name_offset > 0)?;

        let mut sprites = vec![];
        let mut i;
        for offset in sprite_offsets {
            i = &input[start_offset + offset..];
            let (_, sprite) = parse_sprite(i)?;
            sprites.push(sprite);
        }

        let mut scripts = HashMap::new();
        for (index, offset) in script_offsets {
            i = &input[start_offset + offset..];
            let mut instruction_offsets = vec![];

            let mut instructions = vec![];
            loop {
                let tell = input.len() - i.len();
                instruction_offsets.push(tell - (start_offset + offset));
                let (i2, time) = le_u16(i)?;
                let (i2, opcode) = le_u8(i2)?;
                // TODO: maybe check against the size of parsed data?
                let (i2, _size) = le_u8(i2)?;
                let (i2, instr) = parse_instruction_args(i2, opcode)?;
                instructions.push(Call { time, instr });
                i = i2;
                if opcode == 0 {
                    break;
                }
            }
            let mut interrupts = HashMap::new();
            let mut j = 0;
            for Call { time: _, instr } in &mut instructions {
                match instr {
                    Instruction::Jump(ref mut offset) => {
                        let result = instruction_offsets.binary_search(&(*offset as usize));
                        match result {
                            Ok(ptr) => *offset = ptr as u32,
                            // TODO: make that a recoverable error instead.
                            Err(ptr) => panic!("Instruction offset not found for pointer: {}", ptr),
                        }
                    }
                    Instruction::InterruptLabel(interrupt) => {
                        interrupts.insert(*interrupt, j + 1);
                    }
                    _ => ()
                }
                j += 1;
            }
            scripts.insert(index, Script {
                instructions,
                interrupts,
            });
        }

        assert!(has_data == 0);

        let anm0 = Anm0 {
            size: (width, height),
            format,
            first_name,
            second_name,
            sprites,
            scripts,
        };
        list.push(anm0);
        break;
    }
    Ok((b"", list))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{self, Read};
    use std::fs::File;

    #[test]
    fn anm0() {
        let file = File::open("/home/linkmauve/games/pc/東方/TH06 ~ The Embodiment of Scarlet Devil/CM/player01.anm").unwrap();
        let mut file = io::BufReader::new(file);
        let mut buf = vec![];
        file.read_to_end(&mut buf).unwrap();
        let anm0 = Anm0::from_slice(&buf).unwrap();
        assert_eq!(anm0.size, (256, 256));
        assert_eq!(anm0.format, 5);
    }
}
