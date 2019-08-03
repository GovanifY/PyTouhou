//! PBG3 archive files handling.
//!
//! This module provides classes for handling the PBG3 file format.
//! The PBG3 format is the archive format used by Touhou 6: EoSD.
//!
//! PBG3 files are merely a bitstream composed of a header, a file
//! table, and LZSS-compressed files.

use crate::util::bitstream::BitStream;
use crate::util::lzss;
use std::io;
use std::collections::hash_map::{self, HashMap};

/// Helper struct to handle strings and integers in PBG3 bitstreams.
pub struct PBG3BitStream<R: io::Read + io::Seek> {
    bitstream: BitStream<R>,
}

impl<R: io::Read + io::Seek> PBG3BitStream<R> {
    /// Create a bitstream capable of reading u32 and strings.
    pub fn new(bitstream: BitStream<R>) -> PBG3BitStream<R> {
        PBG3BitStream {
            bitstream,
        }
    }

    /// Seek inside the bitstream, ditching any unused data read.
    pub fn seek(&mut self, seek_from: io::SeekFrom) -> io::Result<u64> {
        self.bitstream.seek(seek_from)
    }

    /// Return the current position in the stream.
    pub fn tell(&mut self) -> io::Result<u64> {
        self.bitstream.seek(io::SeekFrom::Current(0))
    }

    /// Read a given amount of bits.
    pub fn read(&mut self, nb_bits: usize) -> io::Result<usize> {
        self.bitstream.read(nb_bits)
    }

    /// Read a given amount of bytes.
    pub fn read_bytes(&mut self, nb_bytes: usize) -> io::Result<Vec<u8>> {
        self.bitstream.read_bytes(nb_bytes)
    }

    /// Read an integer from the bitstream.
    ///
    /// Integers have variable sizes. They begin with a two-bit value indicating
    /// the number of (non-aligned) bytes to read.
    pub fn read_u32(&mut self) -> io::Result<u32> {
        let size = self.read(2)?;
        Ok(self.read((size + 1) * 8)? as u32)
    }

    /// Read a string from the bitstream.
    ///
    /// Strings are stored as NULL-terminated sequences of bytes.
    /// The only catch is that they are not byte-aligned.
    pub fn read_string(&mut self, mut max_size: usize) -> io::Result<Vec<u8>> {
        let mut buf = Vec::new();
        while max_size > 0 {
            let byte = self.read(8)? as u8;
            if byte == 0 {
                break;
            }
            buf.push(byte);
            max_size -= 1;
        }
        Ok(buf)
    }
}

type Entry = (u32, u32, u32, u32, u32);

/// Handle PBG3 archive files.
///
/// PBG3 is a file archive format used in Touhou 6: EoSD.
/// This class provides a representation of such files, as well as functions to
/// read and extract files from a PBG3 archive.
pub struct PBG3<R: io::Read + io::Seek> {
    /// List of PBG3Entry objects describing files present in the archive.
    entries: HashMap<String, Entry>,

    /// PBG3BitStream struct.
    bitstream: PBG3BitStream<R>,
}

impl<R: io::Read + io::Seek> PBG3<R> {
    /// Create a PBG3 archive.
    fn new(entries: HashMap<String, Entry>, bitstream: PBG3BitStream<R>) -> PBG3<R> {
        PBG3 {
            entries,
            bitstream,
        }
    }

    /// Open a PBG3 archive.
    pub fn from_file(mut file: R) -> io::Result<PBG3<R>> {
        let mut magic = [0; 4];
        file.read(&mut magic)?;
        if &magic != b"PBG3" {
            return Err(io::Error::new(io::ErrorKind::Other, "Wrong magic!"));
        }

        let bitstream = BitStream::new(file);
        let mut bitstream = PBG3BitStream::new(bitstream);
        let mut entries = HashMap::new();

        let nb_entries = bitstream.read_u32()?;
        let offset = bitstream.read_u32()?;
        bitstream.seek(io::SeekFrom::Start(offset as u64))?;

        for _ in 0..nb_entries {
            let unknown_1 = bitstream.read_u32()?;
            let unknown_2 = bitstream.read_u32()?;
            let checksum = bitstream.read_u32()?; // Checksum of *compressed data*
            let offset = bitstream.read_u32()?;
            let size = bitstream.read_u32()?;
            let name = bitstream.read_string(255)?;
            // XXX: no unwrap!
            let name = String::from_utf8(name).unwrap();
            entries.insert(name, (unknown_1, unknown_2, checksum, offset, size));
        }

        Ok(PBG3::new(entries, bitstream))
    }

    /// List all file entries in this PBG3 archive.
    pub fn list_files(&self) -> hash_map::Keys<String, Entry> {
        self.entries.keys()
    }

    /// Read a single file from this PBG3 archive.
    pub fn get_file(&mut self, filename: String, check: bool) -> io::Result<Vec<u8>> {
        // XXX: no unwrap!
        let (_unknown_1, _unknown_2, checksum, offset, size) = self.entries.get(&filename).unwrap();
        self.bitstream.seek(io::SeekFrom::Start(*offset as u64))?;
        let data = lzss::decompress(&mut self.bitstream.bitstream, *size as usize, 0x2000, 13, 4, 3)?;
        if check {
            // Verify the checksum.
            let compressed_size = self.bitstream.tell()? as u32 - *offset;
            self.bitstream.seek(io::SeekFrom::Start(*offset as u64))?;
            let mut value: u32 = 0;
            for c in self.bitstream.read_bytes(compressed_size as usize)? {
                value += c as u32;
                value &= 0xffffffff;
            }
            if value != *checksum {
                return Err(io::Error::new(io::ErrorKind::Other, "Corrupted data!"));
            }
        }
        Ok(data)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::util::SeekableSlice;
    use std::fs::File;

    #[test]
    fn bitstream() {
        let data = SeekableSlice::new(b"Hello world!\0");
        let bitstream = BitStream::new(data);
        let mut pbg3 = PBG3BitStream::new(bitstream);
        assert_eq!(pbg3.read_string(42).unwrap(), b"Hello world!");
    }

    #[test]
    fn file_present() {
        let file = File::open("EoSD/MD.DAT").unwrap();
        let file = io::BufReader::new(file);
        let pbg3 = PBG3::from_file(file).unwrap();
        let files = pbg3.list_files().cloned().collect::<Vec<String>>();
        assert!(files.contains(&String::from("th06_01.pos")));
    }

    #[test]
    fn check_all_files() {
        let file = File::open("EoSD/MD.DAT").unwrap();
        let file = io::BufReader::new(file);
        let mut pbg3 = PBG3::from_file(file).unwrap();
        let files = pbg3.list_files().cloned().collect::<Vec<String>>();
        for filename in files {
            pbg3.get_file(filename, true).unwrap();
        }
    }
}
