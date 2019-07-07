//! Animation runner.

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum Formula {
    Linear,
    Power2,
    InvertPower2,
}

impl Formula {
    fn apply(&self, x: f32) -> f32 {
        match self {
            Formula::Linear => x,
            Formula::Power2 => x * x,
            Formula::InvertPower2 => 2. * x - x * x,
        }
    }
}

macro_rules! generate_interpolator {
    ($name:ident, $n:tt) => {
        #[derive(Debug, Clone)]
        pub(crate) struct $name<T> {
            start_values: [T; $n],
            end_values: [T; $n],
            start_frame: u16,
            end_frame: u16,
            formula: Formula,
        }

        impl<T> $name<T>
        where f32: From<T>,
              T: From<f32>,
              T: std::ops::Sub<Output = T>,
              T: std::ops::Add<Output = T>,
              T: Copy,
              T: Default,
        {
            pub fn new(start_values: [T; $n], start_frame: u16, end_values: [T; $n], end_frame: u16, formula: Formula) -> $name<T> {
                $name {
                    start_values,
                    end_values,
                    start_frame,
                    end_frame,
                    formula,
                }
            }

            // XXX: Make it return [T; $n] instead, we don’t want to only do f32 here.
            pub fn values(&self, frame: u16) -> [f32; $n] {
                if frame + 1 >= self.end_frame {
                    // XXX: skip the last interpolation step.
                    // This bug is replicated from the original game.
                    //self.start_frame = self.end_frame;
                    //self.end_values
                    let mut values: [f32; $n] = [Default::default(); $n];
                    for (i, value) in self.end_values.iter().enumerate() {
                        values[i] = f32::from(*value);
                    }
                    values
                } else {
                    let mut coeff = (frame - self.start_frame) as f32 / (self.end_frame - self.start_frame) as f32;
                    coeff = self.formula.apply(coeff);
                    let mut values: [f32; $n] = [Default::default(); $n];
                    for (i, (start, end)) in self.start_values.iter().zip(&self.end_values).enumerate() {
                        values[i] = f32::from(*start + T::from(coeff * f32::from(*end - *start)));
                    }
                    values
                }
            }
        }
    };
}

generate_interpolator!(Interpolator1, 1);
generate_interpolator!(Interpolator2, 2);
generate_interpolator!(Interpolator3, 3);
