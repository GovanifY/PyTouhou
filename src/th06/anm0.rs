//! ANM0 animation format support.

use nom::{
    IResult,
    bytes::complete::{tag, take_while_m_n},
    number::complete::{le_u8, le_u16, le_u32, le_f32},
};
use std::collections::HashMap;

/// Coordinates of a sprite into the image.
#[derive(Debug, Clone)]
pub struct Sprite {
    index: u32,
    x: f32,
    y: f32,
    width: f32,
    height: f32,
}

/// A single instruction, part of a `Script`.
#[derive(Debug, Clone)]
struct Instruction {
    time: u16,
    opcode: u8,
    args: Vec<Arg>,
}

/// Script driving an animation.
#[derive(Debug, Clone)]
pub struct Script {
    instructions: Vec<Instruction>,
    interrupts: HashMap<u32, u8>
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

#[derive(Debug, Clone, Copy)]
enum Arg {
    U8(u8),
    U32(u32),
    F32(f32),
    Ptr(u8),
}

fn parse_u8_arg(i: &[u8]) -> IResult<&[u8], Arg> {
    let (i, value) = le_u8(i)?;
    Ok((i, Arg::U8(value)))
}

fn parse_u32_arg(i: &[u8]) -> IResult<&[u8], Arg> {
    let (i, value) = le_u32(i)?;
    Ok((i, Arg::U32(value)))
}

fn parse_f32_arg(i: &[u8]) -> IResult<&[u8], Arg> {
    let (i, value) = le_f32(i)?;
    Ok((i, Arg::F32(value)))
}

macro_rules! declare_anm_instructions {
    ($($opcode:tt => fn $name:ident($($arg:ident: $arg_type:ty),*)),*,) => {
        fn parse_instruction_args(input: &[u8], opcode: u8) -> IResult<&[u8], Vec<Arg>> {
            let mut args = vec![];
            let mut i = &input[..];
            match opcode {
                $(
                    $opcode => {
                        $(
                            let (i2, data) = match stringify!($arg_type) {
                                "u8" => parse_u8_arg(i),
                                "u32" => parse_u32_arg(i),
                                "f32" => parse_f32_arg(i),
                                "x8" => parse_u8_arg(i),
                                _ => unreachable!(),
                            }?;
                            i = i2;
                            if stringify!($arg_type) != "x8" {
                                args.push(data);
                            }
                        )*
                    }
                )*
                _ => unreachable!()
            }
            Ok((i, args))
        }
    };
}

declare_anm_instructions!{
    0 => fn delete(),
    1 => fn set_sprite(sprite_number: u32),
    2 => fn set_scale(sx: f32, sy: f32),
    3 => fn set_alpha(alpha: u32),
    4 => fn set_color(red: u8, green: u8, blue: u8, XXX: x8),
    5 => fn jump(instruction: u32),
    7 => fn toggle_mirrored(),
    9 => fn set_3d_rotations(x: f32, y: f32, z: f32),
    10 => fn set_3d_rotations_speed(x: f32, y: f32, z: f32),
    11 => fn set_scale_speed(sx: f32, sy: f32),
    12 => fn fade(alpha: u32, duration: u32),
    13 => fn set_blendmode_add(),
    14 => fn set_blendmode_alphablend(),
    15 => fn keep_still(),
    16 => fn set_random_sprite(min_index: u32, amplitude: u32),
    17 => fn set_3d_translation(x: f32, y: f32, z: f32),
    18 => fn move_to_linear(x: f32, y: f32, z: f32, duration: u32),
    19 => fn move_to_decel(x: f32, y: f32, z: f32, duration: u32),
    20 => fn move_to_accel(x: f32, y: f32, z: f32, duration: u32),
    21 => fn wait(),
    22 => fn interrupt_label(label: u32),
    23 => fn set_corner_relative_placement(),
    24 => fn wait_ex(),
    25 => fn set_allow_offset(allow: u32), // TODO: better name
    26 => fn set_automatic_orientation(automatic: u32),
    27 => fn shift_texture_x(dx: f32),
    28 => fn shift_texture_y(dy: f32),
    29 => fn set_visible(visible: u32),
    30 => fn scale_in(sx: f32, sy: f32, duration: u32),
    31 => fn TODO(TODO: u32),
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
                let (i2, args) = parse_instruction_args(i2, opcode)?;
                instructions.push(Instruction { time, opcode, args });
                i = i2;
                if opcode == 0 {
                    break;
                }
            }
            let mut interrupts = HashMap::new();
            let mut j = 0;
            for Instruction { time: _, opcode, args } in &mut instructions {
                match opcode {
                    5 => {
                        let offset = match args[0] {
                            Arg::U32(offset) => offset as usize,
                            _ => panic!("Wrong argument type for jump!"),
                        };
                        let result = instruction_offsets.binary_search(&offset);
                        let ptr = match result {
                            Ok(ptr) => ptr as u8,
                            // TODO: make that a recoverable error instead.
                            Err(ptr) => panic!("Instruction offset not found for pointer: {}", ptr),
                        };
                        args[0] = Arg::Ptr(ptr);
                    }
                    22 => {
                        // TODO: maybe also remove this instruction, as the label is already
                        // present.
                        if let Arg::U32(interrupt) = args[0] {
                            interrupts.insert(interrupt, j + 1);
                        } else {
                            panic!("Wrong argument type for interrupt!");
                        }
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
