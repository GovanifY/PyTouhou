//! Bitstream module.

use std::io;

/// Wrapper around any `Read` trait, to allow bit operations.
pub struct BitStream<R: io::Read + io::Seek> {
    io: R,
    remaining_bits: usize,
    byte: u8,
}

impl<R: io::Read + io::Seek> BitStream<R> {
    /// Create a new bitstream.
    pub fn new(io: R) -> BitStream<R> {
        BitStream {
            io,
            remaining_bits: 0,
            byte: 0,
        }
    }

    /// Seek inside the bitstream, ditching any unused data read.
    pub fn seek(&mut self, seek_from: io::SeekFrom) -> io::Result<u64> {
        self.remaining_bits = 0;
        self.byte = 0;
        self.io.seek(seek_from)
    }

    fn fill_byte(&mut self) -> io::Result<()> {
        assert!(self.remaining_bits == 0);

        let mut buf = [0u8; 1];
        self.io.read_exact(&mut buf)?;
        self.byte = buf[0];
        self.remaining_bits = 8;
        Ok(())
    }

    /// Read only one bit from the stream.
    pub fn read_bit(&mut self) -> io::Result<bool> {
        if self.remaining_bits == 0 {
            self.fill_byte()?;
        }
        self.remaining_bits -= 1;
        Ok((self.byte >> self.remaining_bits) & 0x01 != 0)
    }

    /// Read `nb_bits` bits from the stream.
    pub fn read(&mut self, nb_bits: usize) -> io::Result<usize> {
        let mut nb_bits2 = nb_bits;
        let mut value: usize = 0;
        while nb_bits2 > 0 {
            if self.remaining_bits == 0 {
                self.fill_byte()?;
            }
            let read = if nb_bits2 > self.remaining_bits { self.remaining_bits } else { nb_bits2 };
            nb_bits2 -= read;
            self.remaining_bits -= read;
            value |= (self.byte as usize >> self.remaining_bits) << nb_bits2;
        }
        Ok(value & ((1 << nb_bits) - 1))
    }

    /// Read a given amount of bytes.
    pub fn read_bytes(&mut self, nb_bytes: usize) -> io::Result<Vec<u8>> {
        let mut buf = vec![0u8; nb_bytes];
        self.io.read_exact(&mut buf)?;
        Ok(buf)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::util::SeekableSlice;

    #[test]
    fn bit_by_bit() {
        let data = SeekableSlice::new(&[1, 2, 3]);
        let mut bitstream = BitStream::new(data);

        // 1
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), true);

        // 2
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), true);
        assert_eq!(bitstream.read_bit().unwrap(), false);

        // 3
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read_bit().unwrap(), true);
        assert_eq!(bitstream.read_bit().unwrap(), true);

        // Can’t read after the end.
        bitstream.read_bit().unwrap_err();
    }

    #[test]
    fn byte_by_byte() {
        let data = SeekableSlice::new(&[1, 2, 3]);
        let mut bitstream = BitStream::new(data);

        assert_eq!(bitstream.read(8).unwrap(), 1);
        assert_eq!(bitstream.read(8).unwrap(), 2);
        assert_eq!(bitstream.read(8).unwrap(), 3);

        // Can’t read after the end.
        bitstream.read(1).unwrap_err();
    }

    #[test]
    fn unaligned_bytes() {
        let data = SeekableSlice::new(&[0, 129, 1, 128]);
        let mut bitstream = BitStream::new(data);

        assert_eq!(bitstream.read_bit().unwrap(), false);
        assert_eq!(bitstream.read(8).unwrap(), 1);
        assert_eq!(bitstream.read(8).unwrap(), 2);
        assert_eq!(bitstream.read(8).unwrap(), 3);
        assert_eq!(bitstream.read(7).unwrap(), 0);

        // Can’t read after the end.
        bitstream.read(1).unwrap_err();
    }
}
