//! STD background format support.

use nom::{
    IResult,
    bytes::complete::{tag, take_while_m_n},
    number::complete::{le_u8, le_u16, le_u32, le_i32, le_f32},
    sequence::tuple,
    combinator::map,
};
use encoding_rs::SHIFT_JIS;
use std::collections::HashMap;

/// A float position in the 3D space.
#[derive(Debug, Clone)]
pub struct Position {
    /// X component.
    pub x: f32,

    /// Y component.
    pub y: f32,

    /// Z component.
    pub z: f32,
}

/// A 3D box around something.
#[derive(Debug, Clone)]
struct Box3D {
    width: f32,
    height: f32,
    depth: f32,
}

/// A 2D box around something.
#[derive(Debug, Clone)]
pub struct Box2D {
    width: f32,
    height: f32,
}

/// A quad in the 3D space.
#[derive(Debug, Clone)]
pub struct Quad {
    /// The anm script to run for this quad.
    pub anm_script: u16,

    /// The position of this quad in the 3D space.
    pub pos: Position,

    /// The size of this quad.
    pub size_override: Box2D,
}

/// A model formed of multiple quads in space.
#[derive(Debug, Clone)]
pub struct Model {
    /// TODO: find what that is.
    pub unknown: u16,

    /// The bounding box around this model.
    pub bounding_box: [f32; 6],

    /// The quads composing this model.
    pub quads: Vec<Quad>,
}

/// An instance of a model.
#[derive(Debug, Clone)]
pub struct Instance {
    /// The instance identifier.
    pub id: u16,

    /// Where to position the instance of this model.
    pub pos: Position,
}

/// A single instruction, part of a `Script`.
#[derive(Debug, Clone)]
pub struct Call {
    /// Time at which this instruction will be called.
    pub time: u32,

    /// The instruction to call.
    pub instr: Instruction,
}

/// Parse a SHIFT_JIS byte string of length 128 into a String.
pub fn le_String(i: &[u8]) -> IResult<&[u8], String> {
    let data = i.splitn(2, |c| *c == b'\0').nth(0).unwrap();
    let (string, encoding, replaced) = SHIFT_JIS.decode(data);
    Ok((&i[128..], string.into_owned()))
}

/// Main struct of the STD stage format.
#[derive(Debug, Clone)]
pub struct Stage {
    /// The name of the stage.
    pub name: String,

    /// A list of (name, path) of background music.
    // TODO: there are maximum four of them, and in practice never more than 2.
    pub musics: Vec<Option<(String, String)>>,

    /// List of models.
    pub models: Vec<Model>,

    /// List of instances.
    pub instances: Vec<Instance>,

    /// List of instructions in the script.
    pub script: Vec<Call>,
}

impl Stage {
    /// Parse a slice of bytes into an `Stage` struct.
    pub fn from_slice(data: &[u8]) -> IResult<&[u8], Stage> {
        parse_stage(data)
    }
}

macro_rules! declare_stage_instructions {
    ($($opcode:tt => fn $name:ident($($arg:ident: $arg_type:ident),*)),*,) => {
        /// Available instructions in an `Stage`.
        #[allow(missing_docs)]
        #[derive(Debug, Clone, Copy)]
        pub enum Instruction {
            $(
                $name($($arg_type),*)
            ),*
        }

        fn parse_instruction_args(input: &[u8], opcode: u16) -> IResult<&[u8], Instruction> {
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

declare_stage_instructions!{
    0 => fn SetViewpos(x: f32, y: f32, z: f32),
    1 => fn SetFog(r: u8, g: u8, b: u8, a: u8, near: f32, far: f32),
    2 => fn SetViewpos2(x: f32, y: f32, z: f32),
    3 => fn StartInterpolatingViewpos2(frame: i32, _unused: i32, _unused: i32),
    4 => fn StartInterpolatingFog(frame: i32, _unused: i32, _unused: i32),
    5 => fn Unknown(_unused: i32, _unused: i32, _unused: i32),
}

fn parse_stage(input: &[u8]) -> IResult<&[u8], Stage> {
    let start_offset = 0;
    let i = &input[start_offset..];
    let (i, (num_models, num_faces, object_instances_offset, script_offset, _)) = tuple((le_u16, le_u16, le_u32, le_u32, tag(b"\0\0\0\0")))(i)?;
    let object_instances_offset = object_instances_offset as usize;
    let script_offset = script_offset as usize;

    let (i, name) = le_String(i)?;
    let (i, music_names) = map(tuple((le_String, le_String, le_String, le_String)), |(a, b, c, d)| [a, b, c, d])(i)?;
    let (mut i, music_paths) = map(tuple((le_String, le_String, le_String, le_String)), |(a, b, c, d)| [a, b, c, d])(i)?;
    let musics = music_names.iter().zip(&music_paths).map(|(name, path)| if name == " " { None } else { Some((name.clone(), path.clone())) }).collect();

    let mut offsets = vec![];
    for _ in 0..num_models {
        let (i2, offset) = le_u32(i)?;
        offsets.push(offset as usize);
        i = i2;
    }

    // Read model definitions.
    let mut models = vec![];
    for offset in offsets {
        let i = &input[offset..];
        let (mut i, (id, unknown, x, y, z, width, height, depth)) = tuple((le_u16, le_u16, le_f32, le_f32, le_f32, le_f32, le_f32, le_f32))(i)?;
        let bounding_box = [x, y, z, width, height, depth];
        let mut quads = vec![];
        loop {
            let (i2, (unk1, size)) = tuple((le_u16, le_u16))(i)?;
            if unk1 == 0xffff {
                break;
            }
            assert_eq!(size, 0x1c);
            let (i2, (anm_script, _, x, y, z, width, height)) = tuple((le_u16, tag(b"\0\0"), le_f32, le_f32, le_f32, le_f32, le_f32))(i2)?;
            let quad = Quad {
                anm_script,
                pos: Position { x, y, z },
                size_override: Box2D { width, height },
            };
            quads.push(quad);
            i = i2;
        }
        let model = Model {
            unknown,
            bounding_box,
            quads,
        };
        models.push(model);
    }

    // Read object usage.
    let mut instances = vec![];
    let mut i = &input[object_instances_offset..];
    loop {
        let (i2, (id, unknown, x, y, z)) = tuple((le_u16, le_u16, le_f32, le_f32, le_f32))(i)?;
        if id == 0xffff && unknown == 0xffff {
            break;
        }
        assert_eq!(unknown, 0x100);
        let instance = Instance {
            id,
            pos: Position { x, y, z },
        };
        instances.push(instance);
        i = i2;
    }

    // Read the script.
    let mut script = vec![];
    let mut i = &input[script_offset..];
    loop {
        let (i2, (time, opcode, size)) = tuple((le_u32, le_u16, le_u16))(i)?;
        if time == 0xffffffff && opcode == 0xffff && size == 0xffff {
            break;
        }
        assert_eq!(size, 12);
        let data = &i2[..12];
        let (data, instr) = parse_instruction_args(data, opcode)?;
        assert_eq!(data.len(), 0);
        println!("{:?}", instr);
        script.push(Call { time, instr });
        i = &i2[12..];
    }

    let stage = Stage {
        name,
        musics,
        models,
        instances,
        script,
    };
    Ok((b"", stage))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{self, Read};
    use std::fs::File;

    #[test]
    fn std() {
        let file = File::open("EoSD/ST/stage1.std").unwrap();
        let mut file = io::BufReader::new(file);
        let mut buf = vec![];
        file.read_to_end(&mut buf).unwrap();
        let (_, stage) = Stage::from_slice(&buf).unwrap();
        assert_eq!(stage.name, "夢幻夜行絵巻　～ Mystic Flier");
        assert_eq!(stage.musics.len(), 4);
        assert_eq!(stage.models.len(), 13);
        assert_eq!(stage.instances.len(), 90);
        assert_eq!(stage.script.len(), 21);
    }
}
