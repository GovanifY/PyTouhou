//! Module containing a bunch of helper modules.

pub mod bitstream;
pub mod lzss;
pub mod math;

#[cfg(test)]
use std::io;

#[cfg(test)]
pub struct SeekableSlice<'a> {
    slice: &'a [u8],
    cursor: usize,
}

#[cfg(test)]
impl SeekableSlice<'_> {
    pub fn new(slice: &[u8]) -> SeekableSlice {
        SeekableSlice {
            slice,
            cursor: 0,
        }
    }
}

#[cfg(test)]
impl io::Read for SeekableSlice<'_> {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        let length = (&self.slice[self.cursor..]).read(buf)?;
        self.cursor += length;
        Ok(length)
    }
}

#[cfg(test)]
impl io::Seek for SeekableSlice<'_> {
    fn seek(&mut self, seek_from: io::SeekFrom) -> io::Result<u64> {
        match seek_from {
            io::SeekFrom::Start(offset) => {
                self.cursor = offset as usize;
            }
            io::SeekFrom::End(offset) => {
                self.cursor = (self.slice.len() as i64 + offset) as usize;
            }
            io::SeekFrom::Current(offset) => {
                self.cursor = (self.cursor as i64 + offset) as usize;
            }
        }
        Ok(self.cursor as u64)
    }
}
