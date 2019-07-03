//! LZSS implementation.

use std::io;
use crate::util::bitstream::BitStream;

/// Decompresses a LZSS-compressed file.
pub fn decompress<R: io::Read + io::Seek>(bitstream: &mut BitStream<R>, size: usize, dictionary_size: usize, offset_size: usize, length_size: usize, minimum_match_length: usize) -> io::Result<Vec<u8>> {
    let mut data = vec![0; size];
    let mut dictionary = vec![0; dictionary_size];
    let mut dictionary_head = 1;
    let mut ptr = 0;

    while ptr < size {
        if bitstream.read_bit()? {
            // The `flag` bit is set, indicating the upcoming chunk of data is a literal.
            // Add it to the uncompressed file, and store it in the dictionary.
            let byte = bitstream.read(8)? as u8;
            dictionary[dictionary_head] = byte;
            dictionary_head = (dictionary_head + 1) % dictionary_size;
            data[ptr] = byte;
            ptr += 1;
        } else {
            // The `flag` bit is not set, the upcoming chunk is a (offset, length) tuple.
            let offset = bitstream.read(offset_size)?;
            let length = bitstream.read(length_size)? + minimum_match_length;
            if ptr + length > size {
                return Err(io::Error::new(io::ErrorKind::Other, "Oh no!"));
            }
            if offset == 0 && length == 0 {
                break;
            }
            for i in offset..offset + length {
                data[ptr] = dictionary[i % dictionary_size];
                dictionary[dictionary_head] = dictionary[i % dictionary_size];
                dictionary_head = (dictionary_head + 1) % dictionary_size;
                ptr += 1;
            }
        }
    }

    Ok(data)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::util::SeekableSlice;

    #[test]
    #[ignore]
    fn bit_by_bit() {
        // TODO: find actual lzss data.
        let data = SeekableSlice::new(&[0, 0, 0]);
        let mut bitstream = BitStream::new(data);
        decompress(&mut bitstream, 3, 0x2000, 13, 4, 3).unwrap();
    }
}
