//! Various helpers to deal with vectors and matrices.

/// A 4×4 f32 matrix type.
pub struct Mat4 {
    inner: [[f32; 4]; 4]
}

impl Mat4 {
    /// Create a new matrix from a set of 16 f32.
    pub fn new(inner: [[f32; 4]; 4]) -> Mat4 {
        Mat4 {
            inner
        }
    }

    fn zero() -> Mat4 {
        Mat4 {
            inner: [[0.; 4]; 4]
        }
    }

    fn identity() -> Mat4 {
        Mat4 {
            inner: [[1., 0., 0., 0.],
                    [0., 1., 0., 0.],
                    [0., 0., 1., 0.],
                    [0., 0., 0., 1.]]
        }
    }

    /// Immutably borrow the array of f32 inside this matrix.
    pub fn borrow_inner(&self) -> &[[f32; 4]; 4] {
        &self.inner
    }

    /// Scale the matrix in 2D.
    pub fn scale2d(&mut self, x: f32, y: f32) {
        for i in 0..4 {
            self.inner[0][i] *= x;
            self.inner[1][i] *= y;
        }
    }

    /// Flip the matrix.
    pub fn flip(&mut self) {
        for i in 0..4 {
            self.inner[0][i] = -self.inner[0][i];
        }
    }

    /// Rotate the matrix around its x angle (in radians).
    pub fn rotate_x(&mut self, angle: f32) {
        let mut lines: [f32; 8] = [0.; 8];
        let cos_a = angle.cos();
        let sin_a = angle.sin();
        for i in 0..4 {
            lines[    i] = self.inner[0][i];
            lines[4 + i] = self.inner[1][i];
        }
        for i in 0..4 {
            self.inner[1][i] = cos_a * lines[i] - sin_a * lines[4+i];
            self.inner[2][i] = sin_a * lines[i] + cos_a * lines[4+i];
        }
    }

    /// Rotate the matrix around its y angle (in radians).
    pub fn rotate_y(&mut self, angle: f32) {
        let mut lines: [f32; 8] = [0.; 8];
        let cos_a = angle.cos();
        let sin_a = angle.sin();
        for i in 0..4 {
            lines[    i] = self.inner[0][i];
            lines[4 + i] = self.inner[2][i];
        }
        for i in 0..4 {
            self.inner[0][i] =  cos_a * lines[i] + sin_a * lines[4+i];
            self.inner[2][i] = -sin_a * lines[i] + cos_a * lines[4+i];
        }
    }

    /// Rotate the matrix around its z angle (in radians).
    pub fn rotate_z(&mut self, angle: f32) {
        let mut lines: [f32; 8] = [0.; 8];
        let cos_a = angle.cos();
        let sin_a = angle.sin();
        for i in 0..4 {
            lines[    i] = self.inner[0][i];
            lines[4 + i] = self.inner[1][i];
        }
        for i in 0..4 {
            self.inner[0][i] = cos_a * lines[i] - sin_a * lines[4+i];
            self.inner[1][i] = sin_a * lines[i] + cos_a * lines[4+i];
        }
    }

    /// Translate the matrix by a 3D offset.
    pub fn translate(&mut self, offset: [f32; 3]) {
        let mut item: [f32; 3] = [0.; 3];
        for i in 0..3 {
            item[i] = self.inner[3][i] * offset[i];
        }
        for i in 0..3 {
            for j in 0..4 {
                self.inner[i][j] += item[i];
            }
        }
    }

    /// Translate the matrix by a 2D offset.
    pub fn translate_2d(&mut self, x: f32, y: f32) {
        let offset = [x, y, 0.];
        self.translate(offset);
    }
}

impl std::ops::Mul<Mat4> for Mat4 {
    type Output = Mat4;
    fn mul(self, rhs: Mat4) -> Mat4 {
        let mut tmp = Mat4::zero();
        for i in 0..4 {
            for j in 0..4 {
                for k in 0..4 {
                    tmp.inner[i][j] += self.inner[i][k] * rhs.inner[k][j];
                }
            }
        }
        tmp
    }
}

/// Create an orthographic projection matrix.
pub fn ortho_2d(left: f32, right: f32, bottom: f32, top: f32) -> Mat4 {
    let mut mat = Mat4::identity();
    mat.inner[0][0] = 2. / (right - left);
    mat.inner[1][1] = 2. / (top - bottom);
    mat.inner[2][2] = -1.;
    mat.inner[3][0] = -(right + left) / (right - left);
    mat.inner[3][1] = -(top + bottom) / (top - bottom);
    mat
}

/// Setup a camera view matrix.
pub fn setup_camera(dx: f32, dy: f32, dz: f32) -> Mat4 {
    // Some explanations on the magic constants:
    // 192. = 384. / 2. = width / 2.
    // 224. = 448. / 2. = height / 2.
    // 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
    // This is so that objects on the (O, x, y) plane use pixel coordinates
    look_at([192., 224., -835.979370 * dz], [192. + dx, 224. - dy, 0.], [0., -1., 0.])
}

/// Creates a perspective projection matrix.
pub fn perspective(fov_y: f32, aspect: f32, z_near: f32, z_far: f32) -> Mat4 {
    let top = (fov_y / 2.).tan() * z_near;
    let bottom = -top;
    let left = -top * aspect;
    let right = top * aspect;

    let mut mat = Mat4::identity();
    mat.inner[0][0] = (2. * z_near) / (right - left);
    mat.inner[1][1] = (2. * z_near) / (top - bottom);
    mat.inner[2][2] = -(z_far + z_near) / (z_far - z_near);
    mat.inner[2][3] = -1.;
    mat.inner[3][2] = -(2. * z_far * z_near) / (z_far - z_near);
    mat.inner[3][3] = 0.;
    mat
}

type Vec3 = [f32; 3];

fn look_at(eye: Vec3, center: Vec3, up: Vec3) -> Mat4 {
    let f = normalize(sub(center, eye));
    let u = normalize(up);
    let s = normalize(cross(f, u));
    let u = cross(s, f);

    Mat4::new([[s[0], u[0], -f[0], 0.],
               [s[1], u[1], -f[1], 0.],
               [s[2], u[2], -f[2], 0.],
               [-dot(s, eye), -dot(u, eye), dot(f, eye), 1.]])
}

fn sub(a: Vec3, b: Vec3) -> Vec3 {
    [a[0] - b[0],
     a[1] - b[1],
     a[2] - b[2]]
}

fn normalize(vec: Vec3) -> Vec3 {
    let normal = 1. / (vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]).sqrt();
    [vec[0] * normal, vec[1] * normal, vec[2] * normal]
}

fn cross(a: Vec3, b: Vec3) -> Vec3 {
    [a[1] * b[2] - b[1] * a[2],
     a[2] * b[0] - b[2] * a[0],
     a[0] * b[1] - b[0] * a[1]]
}

fn dot(a: Vec3, b: Vec3) -> f32 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}
