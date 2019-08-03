//! Random number generator extracted from EoSD.

/// Pseudo-random number generator from EoSD.
#[derive(Debug)]
pub struct Prng {
    seed: u16,
}

impl Prng {
    /// Create a new pseudo-random number generator from this seed.
    pub fn new(seed: u16) -> Prng {
        Prng {
            seed,
        }
    }

    /// Generates a pseudo-random u16.
    ///
    /// RE’d from 102h.exe@0x41e780
    pub fn get_u16(&mut self) -> u16 {
        let x = (self.seed ^ 0x9630) - 0x6553;
        self.seed = (((x & 0xc000) >> 14) | (x << 2)) & 0xffff;
        self.seed
    }

    /// Combines two u16 into a single u32.
    ///
    /// RE’d from 102h.exe@0x41e7f0
    pub fn get_u32(&mut self) -> u32 {
        ((self.get_u16() as u32) << 16) | self.get_u16() as u32
    }

    /// Transforms an u32 into a f64.
    ///
    /// RE’d from 102h.exe@0x41e820
    pub fn get_f64(&mut self) -> f64 {
        self.get_u32() as f64 / (0x100000000u64 as f64)
    }
}
